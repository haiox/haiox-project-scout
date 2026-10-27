"""
Unit and Integration Tests for Multi-Tenant Interactive Onboarding Wizard
Module: tests/test_onboarding.py
"""

import pytest
import os
from bot.telegram_client import TelegramBotClient
from bot.user_state import UserStateStore, UserProfile
from bot.onboarding_wizard import OnboardingWizard
from bot.mission_control import MissionControl
from core.schemas import RawJobPosting, PlatformType
from bridge.proposal_synthesizer import SynthesizedProposal, SolutionBlueprint


@pytest.fixture
def temp_store(tmp_path):
    store_file = str(tmp_path / "test_user_profiles.json")
    return UserStateStore(storage_path=store_file)


def test_user_state_store_lifecycle(temp_store):
    user = temp_store.get_or_create(user_id="112233", username="testuser")
    assert user.user_id == "112233"
    assert user.step == "NEW"

    user.step = "READY"
    user.delivery_mode = "realtime"
    user.min_budget = 200.0
    temp_store.update_profile(user)

    # Re-instantiate store from same file to test persistence
    reloaded_store = UserStateStore(storage_path=temp_store.storage_path)
    reloaded_user = reloaded_store.get_or_create(user_id="112233")
    assert reloaded_user.step == "READY"
    assert reloaded_user.min_budget == 200.0
    assert len(reloaded_store.get_all_realtime_users()) == 1


def test_onboarding_wizard_renderers():
    txt1, kb1 = OnboardingWizard.step_1_skills()
    assert "Step 1 of 4" in txt1
    assert len(kb1.inline_keyboard) == 3

    txt2, kb2 = OnboardingWizard.step_2_platforms("🐍 Python, Scraping & Bots")
    assert "Step 2 of 4" in txt2
    assert "Python" in txt2

    txt3, kb3 = OnboardingWizard.step_3_budget()
    assert "Step 3 of 4" in txt3

    txt4, kb4 = OnboardingWizard.step_4_mode()
    assert "Step 4 of 4" in txt4

    prof = UserProfile(user_id="123", skill_category="python", min_budget=100.0, delivery_mode="realtime")
    txt5, kb5 = OnboardingWizard.completion_summary(prof)
    assert "Radar Configured Successfully" in txt5
    assert "$100" in txt5


@pytest.mark.asyncio
async def test_mission_control_wizard_progression(temp_store):
    client = TelegramBotClient(dry_run=True)
    mc = MissionControl(bot_client=client, user_store=temp_store)

    chat_id = "556677"

    # 1. User sends /start
    res_start = await mc.handle_text_message(chat_id=chat_id, text="/start", username="dev_john")
    assert res_start["ok"] is True
    user = temp_store.get_or_create(chat_id)
    assert user.step == "SELECTING_SKILLS"
    assert len(client.sent_messages) == 1
    assert "Step 1 of 4" in client.sent_messages[0]["text"]

    # 2. User clicks Python skill
    await mc.handle_callback_query(
        callback_query_id="cb_1",
        chat_id=chat_id,
        message_id=1,
        data="set_skill:python"
    )
    user = temp_store.get_or_create(chat_id)
    assert user.step == "SELECTING_PLATFORM"
    assert "python" in user.skill_keywords
    assert len(client.edited_messages) == 1
    assert "Step 2 of 4" in client.edited_messages[0]["text"]

    # 3. User clicks All Platforms
    await mc.handle_callback_query(
        callback_query_id="cb_2",
        chat_id=chat_id,
        message_id=1,
        data="set_plat:all"
    )
    user = temp_store.get_or_create(chat_id)
    assert user.step == "SELECTING_BUDGET"
    assert user.platforms == ["all"]
    assert len(client.edited_messages) == 2
    assert "Step 3 of 4" in client.edited_messages[1]["text"]

    # 4. User clicks $100+ USD
    await mc.handle_callback_query(
        callback_query_id="cb_3",
        chat_id=chat_id,
        message_id=1,
        data="set_bud:100"
    )
    user = temp_store.get_or_create(chat_id)
    assert user.step == "SELECTING_MODE"
    assert user.min_budget == 100.0
    assert len(client.edited_messages) == 3
    assert "Step 4 of 4" in client.edited_messages[2]["text"]

    # 5. User selects Real-Time Alerts
    await mc.handle_callback_query(
        callback_query_id="cb_4",
        chat_id=chat_id,
        message_id=1,
        data="set_mode:realtime"
    )
    user = temp_store.get_or_create(chat_id)
    assert user.step == "READY"
    assert user.delivery_mode == "realtime"
    assert len(client.edited_messages) == 4
    assert "Radar Configured Successfully" in client.edited_messages[3]["text"]


@pytest.mark.asyncio
async def test_custom_keyword_flow(temp_store):
    client = TelegramBotClient(dry_run=True)
    mc = MissionControl(bot_client=client, user_store=temp_store)
    chat_id = "998877"

    await mc.handle_text_message(chat_id=chat_id, text="/start")

    # Click custom skill
    await mc.handle_callback_query(
        callback_query_id="cb_cust",
        chat_id=chat_id,
        message_id=1,
        data="set_skill:custom"
    )
    user = temp_store.get_or_create(chat_id)
    assert user.step == "AWAITING_CUSTOM_KEYWORD"

    # User types custom keywords
    await mc.handle_text_message(chat_id=chat_id, text="Solana, Rust, Smart Contracts")
    user = temp_store.get_or_create(chat_id)
    assert user.step == "SELECTING_PLATFORM"
    assert "solana" in user.skill_keywords
    assert "rust" in user.skill_keywords
