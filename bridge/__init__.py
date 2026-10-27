"""
Haiox Project Scout - Genesis Bridge & Proposal Synthesizer
Direct integration with Haiox Genesis software foundry principles.
"""

from .genesis_bridge import GenesisBridge, SolutionBlueprint
from .proposal_synthesizer import ProposalSynthesizer, SynthesizedProposal

__all__ = [
    "GenesisBridge",
    "SolutionBlueprint",
    "ProposalSynthesizer",
    "SynthesizedProposal",
]
