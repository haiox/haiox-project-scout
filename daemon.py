"""
Haiox Project Scout - Autonomous 24/7 Pipeline Daemon
Module: daemon.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Ensure root directory in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from dotenv import load_dotenv

# Load local environment
load_dotenv()

from core.schemas import RawJobPosting, UserFilterCriteria, FeedConfig
from ingestion.aggregator import FeedAggregator
from filters.quality_gate import QualityGate, FilterDecision
from prober.target_prober import TargetProber, TargetInspectionResult
from bridge.proposal_synthesizer import ProposalSynthesizer, SynthesizedProposal
from bot.telegram_client import TelegramBotClient
from bot.mission_control import MissionControl


@dataclass
class DaemonStats:
    cycles_completed: int = 0
    total_raw_jobs: int = 0
    jobs_passed_gate: int = 0
    jobs_probed: int = 0
    alerts_dispatched: int = 0
    start_time: float = field(default_factory=time.time)


class ScoutAutonomousDaemon:
    """
    24/7 Autonomous Daemon coordinating the complete opportunity pipeline:
    Inbound Feed Ingestion -> Quality Gate -> Target Ground Truth Probe ->
    Genesis Prototype Synthesis -> Telegram Mission Control Alert.
    """

    def __init__(
        self,
        aggregator: Optional[FeedAggregator] = None,
        criteria: Optional[UserFilterCriteria] = None,
        quality_gate: Optional[QualityGate] = None,
        prober: Optional[TargetProber] = None,
        synthesizer: Optional[ProposalSynthesizer] = None,
        mission_control: Optional[MissionControl] = None,
        poll_interval_seconds: int = 60,
    ):
        self.aggregator = aggregator or FeedAggregator()
        self.criteria = criteria or UserFilterCriteria(
            min_price=float(os.environ.get("MIN_PRICE_USD", "15.0")),
            required_keywords=[k.strip() for k in os.environ.get("REQUIRED_KEYWORDS", "").split(",") if k.strip()],
            payment_verified_only=os.environ.get("PAYMENT_VERIFIED_ONLY", "False").lower() == "true"
        )
        self.quality_gate = quality_gate or QualityGate()
        self.prober = prober or TargetProber()
        self.synthesizer = synthesizer or ProposalSynthesizer()
        
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        admin_chat_id = os.environ.get("ADMIN_CHAT_ID", "").strip()
        
        if mission_control:
            self.mission_control = mission_control
        else:
            bot_client = TelegramBotClient(bot_token=bot_token, dry_run=not bool(bot_token))
            self.mission_control = MissionControl(bot_client=bot_client, admin_chat_id=admin_chat_id)

        self.poll_interval = poll_interval_seconds or int(os.environ.get("DEFAULT_POLL_INTERVAL", "60"))
        self.processed_fingerprints: Set[str] = set()
        self.stats = DaemonStats()
        self._is_running = False

    async def run_single_cycle(self) -> Dict[str, Any]:
        """
        Executes a single end-to-end pipeline scan cycle.
        Returns execution metrics for auditing and reporting.
        """
        self.stats.cycles_completed += 1
        cycle_start = time.time()
        dispatched_in_cycle: List[str] = []

        # 1. Ingestion: Aggregate raw opportunities from all registered drivers
        raw_jobs, _ = await self.aggregator.poll_all()
        self.stats.total_raw_jobs += len(raw_jobs)

        # 2. Gatekeeper: Filter by user price, keywords, and client criteria
        for job in raw_jobs:
            if job.fingerprint in self.processed_fingerprints:
                continue

            decision: FilterDecision = self.quality_gate.evaluate(job, self.criteria)
            if not decision.passed:
                self.processed_fingerprints.add(job.fingerprint)
                continue

            self.stats.jobs_passed_gate += 1

            # 3. Ground Truth: Inspect client target URL if present
            inspection: TargetInspectionResult = await self.prober.probe_job(job)
            if inspection.is_accessible:
                self.stats.jobs_probed += 1

            # 4. Genesis Synthesis: Produce AST prototype and 3-sentence proposal
            proposal: SynthesizedProposal = self.synthesizer.synthesize(
                job=job,
                inspection=inspection,
                overall_score=decision.overall_score
            )

            # 5. Populate Fast In-Memory Opportunity Cache
            from core.job_cache import GLOBAL_OPPORTUNITY_CACHE
            GLOBAL_OPPORTUNITY_CACHE.add(job=job, decision=decision, proposal=proposal)

            # 6. Multi-Tenant Dispatch: Route to real-time users or admin fallback
            realtime_users = self.mission_control.user_store.get_all_realtime_users()
            if realtime_users:
                for u in realtime_users:
                    job_corpus = f"{job.title} {job.description} {' '.join(job.skills)}".lower()
                    matches_skill = any(kw in job_corpus for kw in u.skill_keywords) if u.skill_keywords else True
                    effective_budget = job.budget_max if job.budget_max > 0 else job.budget_min
                    meets_budget = (effective_budget >= u.min_budget) if u.min_budget > 0 else True
                    
                    if matches_skill and meets_budget:
                        dispatched = await self.mission_control.dispatch_opportunity(
                            job=job,
                            proposal=proposal,
                            score=decision.overall_score,
                            target_chat_id=u.user_id
                        )
                        if dispatched:
                            self.stats.alerts_dispatched += 1
                            dispatched_in_cycle.append(job.id)
            else:
                # Default admin fallback if no registered real-time users yet
                dispatched = await self.mission_control.dispatch_opportunity(
                    job=job,
                    proposal=proposal,
                    score=decision.overall_score
                )
                if dispatched:
                    self.stats.alerts_dispatched += 1
                    dispatched_in_cycle.append(job.id)

            self.processed_fingerprints.add(job.fingerprint)

        cycle_duration = round(time.time() - cycle_start, 3)
        return {
            "cycle": self.stats.cycles_completed,
            "duration_seconds": cycle_duration,
            "total_ingested": len(raw_jobs),
            "dispatched_count": len(dispatched_in_cycle),
            "dispatched_ids": dispatched_in_cycle,
        }

    async def run_daemon(self, max_cycles: Optional[int] = None):
        """
        Runs the continuous daemon loop with configurable cycle limit and intervals.
        """
        self._is_running = True
        print(f"[Daemon] Haiox Project Scout daemon initialized. Interval: {self.poll_interval}s")

        try:
            while self._is_running:
                result = await self.run_single_cycle()
                print(f"[Daemon] Cycle {result['cycle']} complete in {result['duration_seconds']}s. Dispatched: {result['dispatched_count']}")

                if max_cycles and self.stats.cycles_completed >= max_cycles:
                    print(f"[Daemon] Reached max cycle limit ({max_cycles}). Stopping gracefully.")
                    break

                await asyncio.sleep(self.poll_interval)
        except asyncio.CancelledError:
            print("[Daemon] Cancelled by orchestrator.")
        finally:
            self._is_running = False

    def stop(self):
        """Signals daemon to stop gracefully."""
        self._is_running = False


if __name__ == "__main__":
    daemon = ScoutAutonomousDaemon()
    print("Testing single execution cycle with live configuration...")
    result = asyncio.run(daemon.run_single_cycle())
    print(f"Cycle result: {result}")
