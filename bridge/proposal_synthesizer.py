"""
Haiox Project Scout - Pain-Killer Proposal Synthesizer
Module: bridge/proposal_synthesizer.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

from dataclasses import dataclass
from typing import Optional
from core.schemas import RawJobPosting
from prober.target_prober import TargetInspectionResult
from .genesis_bridge import GenesisBridge, SolutionBlueprint


@dataclass
class SynthesizedProposal:
    """Complete 3-sentence Pain-Killer proposal package with live code blueprint."""
    job_id: str
    sentence_1_pain_diagnosis: str
    sentence_2_concrete_solution: str
    sentence_3_free_sample_cta: str
    full_proposal_text: str
    blueprint: SolutionBlueprint
    telegram_card_markdown: str


class ProposalSynthesizer:
    """
    Synthesizes laser-focused 3-sentence Pain-Killer proposals:
    1. Pain diagnosis + Ground truth (live evidence from client target URL or stack).
    2. Concrete solution + Exact architecture (zero resume talk).
    3. Live sample / working prototype offer + direct call to action.
    """

    def __init__(self, bridge: Optional[GenesisBridge] = None):
        self.bridge = bridge or GenesisBridge()

    def synthesize(
        self,
        job: RawJobPosting,
        inspection: Optional[TargetInspectionResult] = None,
        overall_score: float = 85.0
    ) -> SynthesizedProposal:
        # Generate AST-verified prototype blueprint
        blueprint = self.bridge.generate_prototype(job, inspection)

        # 1. Sentence 1: Pain Diagnosis & Ground Truth
        if inspection and inspection.is_accessible and inspection.url:
            tech_names = ", ".join(inspection.tech_info.technologies + inspection.tech_info.frameworks) or "web"
            if inspection.tech_info.waf_or_protection:
                s1 = f"I inspected your target system at {inspection.url}; identified your {tech_names} structure and the {inspection.tech_info.waf_or_protection} limits that lead to request throttling and incomplete datasets."
            elif inspection.tech_info.has_public_api:
                s1 = f"I inspected your target at {inspection.url}; confirmed the underlying endpoint structure and payload schema required for high-throughput automated extraction."
            else:
                s1 = f"I analyzed your target URL ({inspection.url}); identified the specific DOM tree and pagination logic needed to extract the complete dataset without drops."
        elif job.target_urls:
            s1 = f"I reviewed your target requirement at {job.target_urls[0]}; pinpointed the exact structural challenge causing friction in your current workflow."
        else:
            s1 = f"I reviewed your project specifications for '{job.title}'; identified the architectural pipeline and data validation logic required to eliminate manual overhead."

        # 2. Sentence 2: Concrete Solution & Exact Tech Stack (Zero Resume Talk)
        s2 = "I have built an asynchronous Python pipeline using httpx with automated backoff, schema normalization, and zero memory leaks that delivers the exact clean JSON/CSV format you need."

        # 3. Sentence 3: Free Sample Offer & Immediate Call to Action
        s3 = "I already have a working prototype ready that extracts the first batch of verified sample records—message me and I will send you the live sample output right now."

        full_text = f"{s1} {s2} {s3}"

        # Telegram Luxury Glass Card Markdown Formatting
        price_display = f"${job.budget_max:,.0f} {job.currency}" if job.budget_max > 0 else f"${job.budget_min:,.0f} {job.currency}"
        if job.budget_max == 0 and job.budget_min == 0:
            price_display = "Negotiable / Unspecified"

        rating_stars = "⭐" * int(min(job.client_rating, 5.0)) if job.client_rating > 0 else "New Client"
        verified_badge = "✅ Verified" if job.payment_verified else "⚠️ Unverified"

        target_display = f"🎯 <b>Target:</b> <code>{inspection.url}</code>\n" if (inspection and inspection.url) else ""

        card_md = f"""⚡ <b>HAIOX PROJECT SCOUT ALERT</b> | Score: <b>{overall_score}/100</b>
━━━━━━━━━━━━━━━━━━━━━━
💼 <b>Project:</b> {job.title}
🌐 <b>Platform:</b> #{job.platform.value.upper()} | 💰 <b>Budget:</b> {price_display}
👤 <b>Client:</b> {rating_stars} ({job.client_rating:.1f}) | {verified_badge}
{target_display}
📝 <b>3-Sentence Pain-Killer Proposal:</b>
<i>\"{full_text}\"</i>

🛠 <b>Genesis Blueprint:</b>
<code>{blueprint.summary}</code>
━━━━━━━━━━━━━━━━━━━━━━
🔗 <a href=\"{job.source_url or '#'}\">View Original Posting</a>
"""

        return SynthesizedProposal(
            job_id=job.id,
            sentence_1_pain_diagnosis=s1,
            sentence_2_concrete_solution=s2,
            sentence_3_free_sample_cta=s3,
            full_proposal_text=full_text,
            blueprint=blueprint,
            telegram_card_markdown=card_md
        )
