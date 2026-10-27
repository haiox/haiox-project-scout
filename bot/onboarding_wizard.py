"""
Haiox Project Scout - Interactive Multi-Tenant Onboarding Wizard
Module: bot/onboarding_wizard.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

from typing import Tuple, Optional
from .telegram_client import InlineKeyboardButton, InlineKeyboardMarkup
from .user_state import UserProfile, SKILL_TAXONOMY


class OnboardingWizard:
    """Renders international English wizard steps and keyboards for user onboarding."""

    @staticmethod
    def step_1_skills() -> Tuple[str, InlineKeyboardMarkup]:
        text = (
            "🔭 <b>Welcome to Haiox Project Scout!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "I am your autonomous opportunity scout. I track top global software contracts, "
            "inspect technical ground truth via Smart Miner, and synthesize AST-verified "
            "prototypes with Genesis AI.\n\n"
            "<b>Step 1 of 4: Select your primary skill category:</b>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🐍 Python, Scraping & Bots", callback_data="set_skill:python"),
                InlineKeyboardButton(text="🤖 AI, LLMs & Agents", callback_data="set_skill:ai"),
            ],
            [
                InlineKeyboardButton(text="🌐 Web & Fullstack", callback_data="set_skill:web"),
                InlineKeyboardButton(text="📱 Mobile Apps", callback_data="set_skill:mobile"),
            ],
            [
                InlineKeyboardButton(text="📊 Data & Analytics", callback_data="set_skill:data"),
                InlineKeyboardButton(text="✍️ Custom Skill...", callback_data="set_skill:custom"),
            ]
        ])
        return text, kb

    @staticmethod
    def prompt_custom_skill() -> Tuple[str, InlineKeyboardMarkup]:
        text = (
            "✍️ <b>Custom Skill Setup:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Please type and send your exact technology or keywords in chat\n"
            "(e.g., <code>Rust, Solana</code> or <code>Shopify, Liquid</code>):"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back to Skill Categories", callback_data="action:restart_wizard")]
        ])
        return text, kb

    @staticmethod
    def step_2_platforms(skill_label: str) -> Tuple[str, InlineKeyboardMarkup]:
        text = (
            f"🎯 <b>Selected Focus:</b> {skill_label}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<b>Step 2 of 4: Which platforms would you like to scout?</b>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🌐 All Platforms (Recommended)", callback_data="set_plat:all"),
            ],
            [
                InlineKeyboardButton(text="Upwork", callback_data="set_plat:upwork"),
                InlineKeyboardButton(text="Freelancer", callback_data="set_plat:freelancer"),
            ],
            [
                InlineKeyboardButton(text="RemoteOK", callback_data="set_plat:remoteok"),
                InlineKeyboardButton(text="Guru", callback_data="set_plat:guru"),
            ],
            [
                InlineKeyboardButton(text="🔙 Back", callback_data="action:restart_wizard")
            ]
        ])
        return text, kb

    @staticmethod
    def step_3_budget() -> Tuple[str, InlineKeyboardMarkup]:
        text = (
            "💰 <b>Step 3 of 4: Select your target minimum budget:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Filter out micro-tasks and specify your target project floor:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💵 Any Budget", callback_data="set_bud:0"),
                InlineKeyboardButton(text="💰 $100+ USD", callback_data="set_bud:100"),
            ],
            [
                InlineKeyboardButton(text="💎 $300+ USD", callback_data="set_bud:300"),
                InlineKeyboardButton(text="👑 $500+ USD", callback_data="set_bud:500"),
            ],
            [
                InlineKeyboardButton(text="🔙 Back", callback_data="action:restart_wizard")
            ]
        ])
        return text, kb

    @staticmethod
    def step_4_mode() -> Tuple[str, InlineKeyboardMarkup]:
        text = (
            "⚙️ <b>Step 4 of 4: Choose your delivery preference:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "How would you like to receive high-value matching opportunities?"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔔 Real-Time Alerts (Instant Radar)", callback_data="set_mode:realtime"),
            ],
            [
                InlineKeyboardButton(text="🔍 On-Demand Search (Manual Only)", callback_data="set_mode:ondemand"),
            ],
            [
                InlineKeyboardButton(text="🔙 Back", callback_data="action:restart_wizard")
            ]
        ])
        return text, kb

    @staticmethod
    def completion_summary(profile: UserProfile) -> Tuple[str, InlineKeyboardMarkup]:
        skill_info = SKILL_TAXONOMY.get(profile.skill_category, {})
        skill_name = profile.custom_keyword or skill_info.get("label", profile.skill_category.upper())
        plat_str = ", ".join([p.capitalize() for p in profile.platforms])
        mode_str = "🔔 Continuous Real-Time Alerts" if profile.delivery_mode == "realtime" else "🔍 On-Demand Query Only"

        text = (
            "🎉 <b>Radar Configured Successfully!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Skill Focus:</b> {skill_name}\n"
            f"🌐 <b>Platforms:</b> {plat_str}\n"
            f"💰 <b>Min Budget:</b> ${profile.min_budget:,.0f} USD\n"
            f"📡 <b>Delivery:</b> {mode_str}\n"
            "⚡ <b>Genesis AI Proposer:</b> Active (AST Verified)\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Your personal opportunity radar is now active. You will only receive contracts tailored specifically to your criteria.</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Search Matching Deals Now", callback_data="action:search_now"),
            ],
            [
                InlineKeyboardButton(text="⚙️ Reconfigure Radar", callback_data="action:restart_wizard"),
            ]
        ])
        return text, kb
