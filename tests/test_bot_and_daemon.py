"""
Unit and Integration Tests for Phase 5 Telegram Mission Control & Autonomous Daemon
Module: tests/test_bot_and_daemon.py
"""

import pytest
import time
from typing import List, Any
from core.schemas import RawJobPosting, PlatformType, UserFilterCriteria
from bot.telegram_client import TelegramBotClient, InlineKeyboardButton, InlineKeyboardMarkup
from bot.mission_control import MissionControl
from daemon import ScoutAutonomousDaemon
from ingestion.base import BaseFeedDriver
from ingestion.aggregator import FeedAggregator
from filters.quality_gate import QualityGate
from prober.target_prober import TargetProber
from bridge.proposal_synthesizer import ProposalSynthesizer, SynthesizedProposal, SolutionBlueprint


@pytest.mark.asyncio
async def test_telegram_client_dry_run():
    client = TelegramBotClient(dry_run=True)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Test", callback_data="test:1")]
    ])
    res = await client.send_message(chat_id="123456", text="Hello Haiox", reply_markup=kb)

    assert res["ok"] is True
    assert len(client.sent_messages) == 1
    sent = client.sent_messages[0]
    assert sent["chat_id"] == "123456"
    assert sent["text"] == "Hello Haiox"
    assert "reply_markup" in sent
    assert sent["reply_markup"]["inline_keyboard"][0][0]["callback_data"] == "test:1"


@pytest.mark.asyncio
async def test_mission_control_callbacks_and_status():
    client = TelegramBotClient(dry_run=True)
    mc = MissionControl(bot_client=client, admin_chat_id="999")

    job = RawJobPosting(
        id="j_mc_1", platform=PlatformType.FREELANCER, title="Python Scraper",
        description="Scrape target", budget_max=200.0, currency="USD"
    )
    proposal = SynthesizedProposal(
        job_id="j_mc_1",
        sentence_1_pain_diagnosis="Diagnosis",
        sentence_2_concrete_solution="Solution",
        sentence_3_free_sample_cta="Sample",
        full_proposal_text="Full Proposal",
        blueprint=SolutionBlueprint(code="print('ok')", language="python"),
        telegram_card_markdown="<b>Alert Card</b>"
    )

    dispatched = await mc.dispatch_opportunity(job, proposal, score=90.0)
    assert dispatched is True
    assert len(client.sent_messages) == 1

    # Test callback approve
    cb_approve = mc.handle_callback("approve:j_mc_1")
    assert cb_approve["action"] == "approve"
    assert "j_mc_1" in mc.approved_jobs

    # Test callback view_code
    cb_code = mc.handle_callback("view_code:j_mc_1")
    assert cb_code["action"] == "view_code"
    assert cb_code["code"] == "print('ok')"

    # Test callback dismiss
    cb_dismiss = mc.handle_callback("dismiss:j_mc_1")
    assert cb_dismiss["action"] == "dismiss"
    assert "j_mc_1" in mc.dismissed_jobs

    # Status summary
    criteria = UserFilterCriteria(min_price=100.0, required_keywords=["python"])
    status_text = mc.get_status_summary(criteria)
    assert "Processed Opportunities:</b> 1" in status_text
    assert "Approved:</b> 1" in status_text
    assert "Dismissed:</b> 1" in status_text


class MockDriver(BaseFeedDriver):
    def __init__(self, jobs: List[RawJobPosting]):
        super().__init__(PlatformType.CUSTOM)
        self._jobs = jobs

    async def fetch_jobs(self) -> List[RawJobPosting]:
        return self._jobs

    def parse_payload(self, raw_data: Any) -> List[RawJobPosting]:
        return self._jobs


@pytest.mark.asyncio
async def test_daemon_end_to_end_single_cycle():
    # 1. Prepare sample jobs: 1 passes filter, 1 fails price, 1 fails keyword
    job_pass = RawJobPosting(
        id="pass_1",
        platform=PlatformType.UPWORK,
        title="High Scale Python Data Pipeline",
        description="Need an async Python scraper for https://ecommerce-site.com/catalog to collect inventory.",
        budget_max=300.0,
        currency="USD",
        payment_verified=True,
        client_rating=4.8,
        published_at=time.time() - 60
    )
    job_fail_price = RawJobPosting(
        id="fail_price",
        platform=PlatformType.FREELANCER,
        title="Python Tiny Task",
        description="Simple script",
        budget_max=20.0,  # Below min_price $100
        currency="USD",
        payment_verified=True,
        client_rating=5.0
    )
    job_fail_kw = RawJobPosting(
        id="fail_kw",
        platform=PlatformType.REMOTEOK,
        title="Ruby Developer",
        description="Ruby on rails developer needed",
        budget_max=500.0,
        currency="USD",
        payment_verified=True,
        client_rating=5.0
    )

    aggregator = FeedAggregator()
    aggregator.drivers = [MockDriver([job_pass, job_fail_price, job_fail_kw])]

    criteria = UserFilterCriteria(
        min_price=100.0,
        required_keywords=["python"],
        payment_verified_only=True
    )

    bot_client = TelegramBotClient(dry_run=True)
    mission_control = MissionControl(bot_client=bot_client, admin_chat_id="ADMIN")

    daemon = ScoutAutonomousDaemon(
        aggregator=aggregator,
        criteria=criteria,
        mission_control=mission_control,
        poll_interval_seconds=1
    )

    # Run single cycle
    cycle_res = await daemon.run_single_cycle()

    assert cycle_res["cycle"] == 1
    assert cycle_res["total_ingested"] == 3
    assert cycle_res["dispatched_count"] == 1
    assert cycle_res["dispatched_ids"] == ["pass_1"]

    # Verify message sent to operator
    assert len(bot_client.sent_messages) == 1
    sent_text = bot_client.sent_messages[0]["text"]
    assert "HAIOX PROJECT SCOUT ALERT" in sent_text
    assert "High Scale Python Data Pipeline" in sent_text

    # Second cycle: verify deduplication prevents re-dispatching
    cycle_res_2 = await daemon.run_single_cycle()
    assert cycle_res_2["cycle"] == 2
    assert cycle_res_2["dispatched_count"] == 0
    assert len(bot_client.sent_messages) == 1  # No duplicate message sent!
