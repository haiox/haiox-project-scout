"""
Haiox Project Scout - Luxury Responsive HTML Solution Blueprint Generator
Module: bridge/html_blueprint.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import html
import time
from typing import Optional
from core.schemas import RawJobPosting
from prober.target_prober import TargetInspectionResult
from .proposal_synthesizer import SynthesizedProposal


class HTMLBlueprintBuilder:
    """
    Synthesizes luxury, ultra-responsive dark glassmorphic HTML solution reports
    featuring project autopsy, 3-phase engineering roadmap, and syntax-highlighted code.
    """

    @staticmethod
    def build(
        job: RawJobPosting,
        proposal: SynthesizedProposal,
        inspection: Optional[TargetInspectionResult] = None,
        overall_score: float = 90.0
    ) -> str:
        safe_title = html.escape(job.title)
        safe_desc = html.escape(job.description[:600])
        safe_code = html.escape(proposal.blueprint.code)
        safe_summary = html.escape(proposal.blueprint.summary)
        
        target_url = inspection.url if (inspection and inspection.url) else (job.target_urls[0] if job.target_urls else "N/A")
        tech_stack = ", ".join(inspection.tech_info.technologies + inspection.tech_info.frameworks) if inspection else "Automated Extraction"
        waf_info = inspection.tech_info.waf_or_protection if inspection else "None detected"

        price_disp = f"${job.budget_max:,.0f} {job.currency}" if job.budget_max > 0 else f"${job.budget_min:,.0f} {job.currency}"
        if job.budget_max == 0 and job.budget_min == 0:
            price_disp = "Negotiable"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Genesis Solution Blueprint &bull; {safe_title[:40]}</title>
    <style>
        :root {{
            --bg-base: #06090e;
            --bg-surface: #0d1117;
            --bg-card: #161b22;
            --border: #30363d;
            --cyan: #00f2fe;
            --ice-blue: #38bdf8;
            --emerald: #10b981;
            --purple: #a855f7;
            --amber: #f59e0b;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background-color: var(--bg-base); color: var(--text-primary); padding: 20px 14px; line-height: 1.6; min-height: 100vh; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        
        /* Header Hero */
        .header {{
            background: linear-gradient(135deg, rgba(13,17,23,0.95), rgba(22,27,34,0.98));
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            position: relative;
            overflow: hidden;
        }}
        .header::before {{
            content: ''; position: absolute; top: 0; right: 0; width: 300px; height: 100%;
            background: radial-gradient(circle at top right, rgba(56, 189, 248, 0.2), transparent 70%);
            pointer-events: none;
        }}
        .badge-pill {{
            display: inline-block;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 4px 12px;
            border-radius: 20px;
            background: rgba(56, 189, 248, 0.15);
            color: var(--ice-blue);
            border: 1px solid var(--ice-blue);
            margin-bottom: 12px;
        }}
        h1 {{ font-size: 22px; font-weight: 800; color: #fff; margin-bottom: 10px; }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid rgba(255,255,255,0.08);
            font-size: 13px;
        }}
        .meta-item b {{ display: block; font-size: 11px; color: var(--text-secondary); text-transform: uppercase; }}
        .meta-item span {{ font-size: 14px; font-weight: 700; color: var(--text-primary); }}

        /* Pain-Killer Proposal Box */
        .proposal-card {{
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .proposal-card h3 {{ font-size: 14px; text-transform: uppercase; color: var(--emerald); margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }}
        .proposal-text {{ font-size: 15px; font-style: italic; color: #e6edf3; line-height: 1.7; }}

        /* 3-Phase Roadmap */
        .section-title {{ font-size: 16px; font-weight: 700; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; color: var(--ice-blue); }}
        .roadmap-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; margin-bottom: 24px; }}
        .phase-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            position: relative;
        }}
        .phase-card.active {{ border-color: var(--cyan); background: rgba(0, 242, 254, 0.03); }}
        .phase-badge {{ font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; display: inline-block; margin-bottom: 8px; }}
        .phase-card h4 {{ font-size: 14px; margin-bottom: 6px; color: #fff; }}
        .phase-card p {{ font-size: 12.5px; color: var(--text-secondary); line-height: 1.5; }}

        /* Code Block */
        .code-container {{
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            overflow: hidden;
            margin-bottom: 24px;
        }}
        .code-header {{
            background: var(--bg-card);
            padding: 12px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
        }}
        .code-header span {{ font-size: 13px; font-weight: 600; color: var(--text-secondary); }}
        .btn-copy {{
            background: var(--ice-blue);
            color: #000;
            border: none;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-copy:hover {{ opacity: 0.9; transform: scale(1.02); }}
        pre {{
            padding: 18px;
            overflow-x: auto;
            font-family: Consolas, "Courier New", monospace;
            font-size: 12.5px;
            color: #79c0ff;
            line-height: 1.6;
        }}

        /* Footer */
        .footer {{ text-align: center; font-size: 12px; color: var(--text-secondary); padding: 14px 0; border-top: 1px solid var(--border); }}
    </style>
</head>
<body>
    <div class="container">
        
        <!-- Header -->
        <header class="header">
            <span class="badge-pill">⚡ Genesis Software Foundry &bull; Score {overall_score}/100</span>
            <h1>{safe_title}</h1>
            <div class="meta-grid">
                <div class="meta-item"><b>Budget</b><span>{price_disp}</span></div>
                <div class="meta-item"><b>Platform</b><span>{job.platform.value.upper()}</span></div>
                <div class="meta-item"><b>Target Tech</b><span>{tech_stack}</span></div>
                <div class="meta-item"><b>WAF / Shield</b><span>{waf_info}</span></div>
            </div>
        </header>

        <!-- Pain-Killer Proposal -->
        <section class="proposal-card">
            <h3>⚡ 3-Sentence Pain-Killer Proposal</h3>
            <p class="proposal-text">"{proposal.full_proposal_text}"</p>
        </section>

        <!-- 3-Phase Execution Roadmap -->
        <h3 class="section-title">📌 Phased Implementation Roadmap</h3>
        <div class="roadmap-grid">
            <div class="phase-card active">
                <span class="phase-badge" style="background: rgba(0, 242, 254, 0.15); color: var(--cyan);">PHASE 1 &bull; DELIVERED</span>
                <h4>Proof of Concept & Extraction</h4>
                <p>Ground truth reconnaissance, target schema normalization, and working AST prototype extracting verified sample records.</p>
            </div>
            <div class="phase-card">
                <span class="phase-badge" style="background: rgba(168, 85, 247, 0.15); color: var(--purple);">PHASE 2 &bull; MILESTONE</span>
                <h4>High-Throughput Engine</h4>
                <p>Asynchronous pagination pipeline, rate-limiting adaptation, concurrency pooling, and automated error recovery.</p>
            </div>
            <div class="phase-card">
                <span class="phase-badge" style="background: rgba(16, 185, 129, 0.15); color: var(--emerald);">PHASE 3 &bull; DELIVERY</span>
                <h4>Validation & Export Integration</h4>
                <p>Automated duplicate stripping, schema validation against clean CSV/JSON/DB, and final deployment documentation.</p>
            </div>
        </div>

        <!-- Code Block -->
        <h3 class="section-title">💻 Genesis AST-Verified Prototype Script</h3>
        <div class="code-container">
            <div class="code-header">
                <span>{safe_summary}</span>
                <button class="btn-copy" onclick="copyCode()">Copy Code</button>
            </div>
            <pre><code id="codeBlock">{safe_code}</code></pre>
        </div>

        <!-- Footer -->
        <footer class="footer">
            Generated autonomously by <b>Haiox Project Scout & Genesis v1.0.0</b> &bull; Sovereign Engineering
        </footer>

    </div>

    <script>
        function copyCode() {{
            const code = document.getElementById('codeBlock').innerText;
            navigator.clipboard.writeText(code).then(() => {{
                const btn = document.querySelector('.btn-copy');
                btn.innerText = 'Copied!';
                setTimeout(() => {{ btn.innerText = 'Copy Code'; }}, 2000);
            }});
        }}
    </script>
</body>
</html>
"""
