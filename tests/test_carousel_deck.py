"""
Unit and Integration Tests for Interactive Carousel Deck & Smart Fallback Navigation
Module: tests/test_carousel_deck.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import pytest
from bot.telegram_client import TelegramBotClient
from bot.mission_control import MissionControl
from bot.user_state import UserStateStore
from core.job_cache import OpportunityCache, GLOBAL_OPPORTUNITY_CACHE, seed_cache_if_empty
from core.schemas import RawJobPosting, PlatformType
from filters.quality_gate import FilterDecision
from bridge.proposal_synthesizer import ProposalSynthesizer


@pytest.fixture
def clean_mc(tmp_path):
    store_file = str(tmp_path / "deck_test_users.json")
    user_store = UserStateStore(storage_path=store_file)
    bot_client = TelegramBotClient(dry_run=True)
    return MissionControl(bot_client=bot_client, user_store=user_store)


@pytest.mark.asyncio
async def test_carousel_deck_search_and_render(clean_mc):
    chat_id = "test_deck_user_1"
    profile = clean_mc.user_store.get_or_create(chat_id)
    profile.skill_keywords = ["python", "scraper"]
    clean_mc.user_store.update_profile(profile)

    res = await clean_mc.execute_user_search(chat_id)
    assert res["ok"] is True
    assert len(clean_mc.client.sent_messages) == 1

    sent = clean_mc.client.sent_messages[0]
    assert "Deal 1 of" in sent["text"]
    assert "Pain Diagnosis:" in sent["text"]
    assert "Proposed Solution:" in sent["text"]

    # Verify Carousel Inline Keyboard structure
    kb = sent["reply_markup"]["inline_keyboard"]
    nav_row = kb[0]
    assert nav_row[0]["text"] == "◀️ Previous"
    assert "Card 1 /" in nav_row[1]["text"]
    assert nav_row[2]["text"] == "Next ▶️"

    # Verify action rows
    action_row_1 = kb[1]
    assert "⚡ Approve & Copy" in action_row_1[0]["text"]
    assert "💻 View Genesis Code" in action_row_1[1]["text"]


@pytest.mark.asyncio
async def test_carousel_deck_navigation(clean_mc):
    chat_id = "test_deck_user_2"
    clean_mc.user_store.get_or_create(chat_id)

    # Initial search
    await clean_mc.execute_user_search(chat_id)
    deck_info = clean_mc.user_search_decks[chat_id]
    total = len(deck_info["opportunities"])
    assert total >= 2

    # Click Next ▶️ from card 0
    await clean_mc.handle_callback_query(
        callback_query_id="cb_next",
        chat_id=chat_id,
        message_id=1,
        data="deck:next:0"
    )

    assert len(clean_mc.client.edited_messages) == 1
    edited = clean_mc.client.edited_messages[0]
    assert "Deal 2 of" in edited["text"]
    assert f"Card 2 / {total}" in edited["reply_markup"]["inline_keyboard"][0][1]["text"]

    # Click ◀️ Previous from card 1 -> back to card 0
    await clean_mc.handle_callback_query(
        callback_query_id="cb_prev",
        chat_id=chat_id,
        message_id=1,
        data="deck:prev:1"
    )

    assert len(clean_mc.client.edited_messages) == 2
    edited_back = clean_mc.client.edited_messages[1]
    assert "Deal 1 of" in edited_back["text"]
    assert f"Card 1 / {total}" in edited_back["reply_markup"]["inline_keyboard"][0][1]["text"]


@pytest.mark.asyncio
async def test_carousel_deck_dismiss_slides_to_next(clean_mc):
    chat_id = "test_deck_user_3"
    clean_mc.user_store.get_or_create(chat_id)

    await clean_mc.execute_user_search(chat_id)
    deck_info = clean_mc.user_search_decks[chat_id]
    initial_total = len(deck_info["opportunities"])
    target_id = deck_info["opportunities"][0].job.id

    # User clicks dismiss
    await clean_mc.handle_callback_query(
        callback_query_id="cb_dismiss",
        chat_id=chat_id,
        message_id=1,
        data=f"dismiss:{target_id}"
    )

    assert target_id in clean_mc.dismissed_jobs
    remaining = clean_mc.user_search_decks[chat_id]["opportunities"]
    assert len(remaining) == initial_total - 1
    assert all(o.job.id != target_id for o in remaining)

    # Message was edited to show the next deal
    assert len(clean_mc.client.edited_messages) == 1
    assert "Deal 1 of" in clean_mc.client.edited_messages[0]["text"]
