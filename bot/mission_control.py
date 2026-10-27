"""
Haiox Project Scout - Multi-Tenant Mission Control & Interactive Wizard Engine
Module: bot/mission_control.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

from typing import Optional, Dict, Any, List, Tuple
from core.schemas import RawJobPosting, UserFilterCriteria
from bridge.proposal_synthesizer import SynthesizedProposal
from .telegram_client import TelegramBotClient, InlineKeyboardButton, InlineKeyboardMarkup
from .user_state import UserStateStore, UserProfile, SKILL_TAXONOMY
from .onboarding_wizard import OnboardingWizard


class MissionControl:
    """
    Public Multi-Tenant Mission Control:
    - Interactive 4-step onboarding wizard (Skills, Platforms, Budget, Real-Time Mode).
    - In-place message updates (zero chat clutter).
    - Instant live opportunity delivery tailored to individual user criteria.
    - 100% pure international English interface.
    """

    def __init__(
        self,
        bot_client: Optional[TelegramBotClient] = None,
        user_store: Optional[UserStateStore] = None,
        admin_chat_id: str = "ADMIN_ID",
    ):
        self.client = bot_client or TelegramBotClient(dry_run=True)
        self.user_store = user_store or UserStateStore()
        self.admin_chat_id = str(admin_chat_id)
        self.stored_proposals: Dict[str, SynthesizedProposal] = {}
        self.approved_jobs: List[str] = []
        self.dismissed_jobs: List[str] = []
        self.user_search_decks: Dict[str, Dict[str, Any]] = {}

    def render_deck_card(
        self,
        opp: Any,
        index: int,
        total: int,
        notice: str = ""
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """Renders an individual card in the interactive carousel deck with 4-row layout."""
        job = opp.job
        proposal = opp.proposal
        score = opp.decision.overall_score
        effective_budget = job.budget_max if job.budget_max > 0 else job.budget_min

        notice_block = f"⚠️ <i>{notice}</i>\n\n" if notice else ""
        skills_str = ", ".join(job.skills[:4]) if job.skills else "Software Engineering"
        platform_name = job.platform.value.upper()

        card_text = (
            f"🎴 <b>Deal {index + 1} of {total}</b> | <b>{platform_name}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{notice_block}"
            f"📌 <b>{job.title}</b>\n"
            f"💰 <b>Budget:</b> ${effective_budget:,.0f} {job.currency}\n"
            f"⭐️ <b>Match & Quality Score:</b> {score:.0f}/100\n"
            f"🛠 <b>Skills:</b> <code>{skills_str}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Pain Diagnosis:</b>\n"
            f"<i>{proposal.sentence_1_pain_diagnosis}</i>\n\n"
            f"⚡ <b>Proposed Solution:</b>\n"
            f"<i>{proposal.sentence_2_concrete_solution}</i>\n\n"
            f"🎁 <b>Free Sample:</b>\n"
            f"<i>{proposal.sentence_3_free_sample_cta}</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Tap ◀️ / ▶️ to browse deals without chat clutter.</i>"
        )

        nav_row = [
            InlineKeyboardButton(text="◀️ Previous", callback_data=f"deck:prev:{index}"),
            InlineKeyboardButton(text=f"Card {index + 1} / {total}", callback_data="deck:noop"),
            InlineKeyboardButton(text="Next ▶️", callback_data=f"deck:next:{index}"),
        ]
        action_row_1 = [
            InlineKeyboardButton(text="⚡ Approve & Copy", callback_data=f"approve:{job.id}"),
            InlineKeyboardButton(text="💻 View Genesis Code", callback_data=f"view_code:{job.id}"),
        ]
        action_row_2 = [
            InlineKeyboardButton(text="🎯 Ground Truth", callback_data=f"ground_truth:{job.id}"),
        ]
        if job.source_url:
            action_row_2.append(InlineKeyboardButton(text="🌐 Open Project", url=job.source_url))

        action_row_3 = [
            InlineKeyboardButton(text="❌ Dismiss", callback_data=f"dismiss:{job.id}"),
            InlineKeyboardButton(text="🔄 Refresh Deals", callback_data="action:search_now"),
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=[nav_row, action_row_1, action_row_2, action_row_3])
        return card_text, keyboard

    def build_opportunity_keyboard(self, job: RawJobPosting) -> InlineKeyboardMarkup:
        """Constructs interactive international English inline keyboard for rapid operations."""
        row_1 = [
            InlineKeyboardButton(text="⚡ Approve & Copy", callback_data=f"approve:{job.id}"),
            InlineKeyboardButton(text="💻 View Genesis Code", callback_data=f"view_code:{job.id}"),
        ]
        row_2 = [
            InlineKeyboardButton(text="🎯 Ground Truth", callback_data=f"ground_truth:{job.id}"),
        ]
        if job.source_url:
            row_2.append(InlineKeyboardButton(text="🌐 Open Project", url=job.source_url))

        row_3 = [
            InlineKeyboardButton(text="❌ Dismiss", callback_data=f"dismiss:{job.id}")
        ]
        return InlineKeyboardMarkup(inline_keyboard=[row_1, row_2, row_3])

    def handle_callback(self, callback_data: str) -> Dict[str, Any]:
        """Convenience processor for synchronous callback evaluation."""
        if not callback_data or ":" not in callback_data:
            return {"action": "unknown", "message": "Unknown action"}

        action, job_id = callback_data.split(":", 1)
        proposal = self.stored_proposals.get(job_id)

        if action == "approve":
            if job_id not in self.approved_jobs:
                self.approved_jobs.append(job_id)
            return {
                "action": "approve",
                "job_id": job_id,
                "message": f"✅ Opportunity {job_id} approved.",
                "proposal_text": proposal.full_proposal_text if proposal else ""
            }

        elif action == "dismiss":
            if job_id not in self.dismissed_jobs:
                self.dismissed_jobs.append(job_id)
            return {
                "action": "dismiss",
                "job_id": job_id,
                "message": f"❌ Opportunity {job_id} dismissed."
            }

        elif action == "view_code":
            code_snippet = proposal.blueprint.code if proposal else "# No code available"
            return {
                "action": "view_code",
                "job_id": job_id,
                "message": "Genesis prototype code ready.",
                "code": code_snippet
            }

        elif action == "ground_truth":
            diagnosis = proposal.sentence_1_pain_diagnosis if proposal else "No ground truth available."
            return {
                "action": "ground_truth",
                "job_id": job_id,
                "message": f"🎯 Ground Truth: {diagnosis}"
            }

        return {"action": "unsupported", "message": "Action not recognized"}

    async def handle_start(self, chat_id: str, username: str = "") -> Dict[str, Any]:
        """Initiates the 4-step interactive onboarding wizard for a new or returning user."""
        profile = self.user_store.get_or_create(chat_id, username)
        profile.step = "SELECTING_SKILLS"
        self.user_store.update_profile(profile)

        text, kb = OnboardingWizard.step_1_skills()
        return await self.client.send_message(chat_id=chat_id, text=text, reply_markup=kb)

    async def handle_callback_query(
        self,
        callback_query_id: str,
        chat_id: str,
        message_id: int,
        data: str
    ) -> Dict[str, Any]:
        """Routes inline keyboard clicks through wizard steps or opportunity actions."""
        profile = self.user_store.get_or_create(chat_id)

        # 1. Wizard Step Transitions
        if data.startswith("set_skill:"):
            cat = data.split(":", 1)[1]
            if cat == "custom":
                profile.step = "AWAITING_CUSTOM_KEYWORD"
                self.user_store.update_profile(profile)
                text, kb = OnboardingWizard.prompt_custom_skill()
                await self.client.edit_message_text(chat_id, message_id, text, reply_markup=kb)
                return await self.client.answer_callback_query(callback_query_id, text="Please type your custom skill.")

            profile.skill_category = cat
            tax = SKILL_TAXONOMY.get(cat, {})
            profile.skill_keywords = tax.get("keywords", [cat])
            profile.step = "SELECTING_PLATFORM"
            self.user_store.update_profile(profile)

            skill_label = tax.get("label", cat.upper())
            text, kb = OnboardingWizard.step_2_platforms(skill_label)
            await self.client.edit_message_text(chat_id, message_id, text, reply_markup=kb)
            return await self.client.answer_callback_query(callback_query_id, text=f"Selected {skill_label}")

        elif data.startswith("set_plat:"):
            plat = data.split(":", 1)[1]
            profile.platforms = ["all"] if plat == "all" else [plat]
            profile.step = "SELECTING_BUDGET"
            self.user_store.update_profile(profile)

            text, kb = OnboardingWizard.step_3_budget()
            await self.client.edit_message_text(chat_id, message_id, text, reply_markup=kb)
            return await self.client.answer_callback_query(callback_query_id, text=f"Platform: {plat.upper()}")

        elif data.startswith("set_bud:"):
            bud = float(data.split(":", 1)[1])
            profile.min_budget = bud
            profile.step = "SELECTING_MODE"
            self.user_store.update_profile(profile)

            text, kb = OnboardingWizard.step_4_mode()
            await self.client.edit_message_text(chat_id, message_id, text, reply_markup=kb)
            return await self.client.answer_callback_query(callback_query_id, text=f"Floor: ${bud:.0f}")

        elif data.startswith("set_mode:"):
            mode = data.split(":", 1)[1]
            profile.delivery_mode = mode
            profile.step = "READY"
            self.user_store.update_profile(profile)

            text, kb = OnboardingWizard.completion_summary(profile)
            await self.client.edit_message_text(chat_id, message_id, text, reply_markup=kb)
            return await self.client.answer_callback_query(callback_query_id, text="Radar Active!")

        elif data == "action:restart_wizard":
            profile.step = "SELECTING_SKILLS"
            self.user_store.update_profile(profile)
            text, kb = OnboardingWizard.step_1_skills()
            await self.client.edit_message_text(chat_id, message_id, text, reply_markup=kb)
            return await self.client.answer_callback_query(callback_query_id, text="Restarting configuration.")

        elif data == "action:search_now":
            await self.client.answer_callback_query(callback_query_id, text="Searching top contracts...")
            return await self.execute_user_search(chat_id)

        # 2. Carousel Deck Navigation
        elif data == "deck:noop":
            deck_info = self.user_search_decks.get(str(chat_id), {})
            total = len(deck_info.get("opportunities", []))
            return await self.client.answer_callback_query(callback_query_id, text=f"Deck contains {total} deals. Use ◀️ / ▶️ to browse.")

        elif data.startswith("deck:prev:") or data.startswith("deck:next:"):
            _, direction, idx_str = data.split(":")
            curr_idx = int(idx_str)

            deck_info = self.user_search_decks.get(str(chat_id))
            if not deck_info or not deck_info.get("opportunities"):
                # Self-healing: query again if missing from memory
                from core.job_cache import GLOBAL_OPPORTUNITY_CACHE
                matches, is_fallback, notice = GLOBAL_OPPORTUNITY_CACHE.search_with_smart_fallback(
                    keywords=profile.skill_keywords,
                    min_budget=profile.min_budget,
                    platforms=profile.platforms,
                    limit=5
                )
                if not matches:
                    return await self.client.answer_callback_query(callback_query_id, text="No deals in deck right now.")
                deck_info = {"opportunities": matches, "notice": notice, "is_fallback": is_fallback}
                self.user_search_decks[str(chat_id)] = deck_info

            opps = deck_info["opportunities"]
            total = len(opps)
            new_idx = (curr_idx - 1) % total if direction == "prev" else (curr_idx + 1) % total

            opp = opps[new_idx]
            self.stored_proposals[opp.job.id] = opp.proposal
            card_text, card_kb = self.render_deck_card(opp, new_idx, total, deck_info.get("notice", ""))

            await self.client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=card_text,
                reply_markup=card_kb,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            return await self.client.answer_callback_query(callback_query_id, text=f"Deal {new_idx + 1} of {total}")

        # 3. Opportunity Card Actions
        elif ":" in data:
            action, job_id = data.split(":", 1)
            proposal = self.stored_proposals.get(job_id)

            if action == "approve":
                if job_id not in self.approved_jobs:
                    self.approved_jobs.append(job_id)
                prop_text = proposal.full_proposal_text if proposal else "Proposal locked."
                await self.client.answer_callback_query(callback_query_id, text="✅ Opportunity approved! Copied to clipboard.", show_alert=True)
                # Send one-tap copy message
                return await self.client.send_message(
                    chat_id=chat_id,
                    text=f"📋 <b>One-Tap Proposal for Job #{job_id}:</b>\n\n<code>{prop_text}</code>"
                )

            elif action == "dismiss":
                if job_id not in self.dismissed_jobs:
                    self.dismissed_jobs.append(job_id)
                await self.client.answer_callback_query(callback_query_id, text="❌ Dismissed and archived.", show_alert=False)

                deck_info = self.user_search_decks.get(str(chat_id))
                if deck_info and deck_info.get("opportunities"):
                    deck_info["opportunities"] = [o for o in deck_info["opportunities"] if o.job.id != job_id]
                    remaining = deck_info["opportunities"]
                    if remaining:
                        opp = remaining[0]
                        self.stored_proposals[opp.job.id] = opp.proposal
                        card_text, card_kb = self.render_deck_card(opp, 0, len(remaining), deck_info.get("notice", ""))
                        return await self.client.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=card_text,
                            reply_markup=card_kb,
                            parse_mode="HTML",
                            disable_web_page_preview=True
                        )
                    else:
                        return await self.client.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text="✅ <b>All Opportunities Reviewed!</b>\n\n<i>All current deals in this deck have been processed. Tap /search to scan for newly ingested contracts.</i>",
                            parse_mode="HTML"
                        )

            elif action == "view_code":
                await self.client.answer_callback_query(callback_query_id, text="Generating Genesis HTML solution...")
                from bridge.html_blueprint import HTMLBlueprintBuilder
                from core.job_cache import GLOBAL_OPPORTUNITY_CACHE

                opp = GLOBAL_OPPORTUNITY_CACHE._cache.get(job_id)
                job = opp.job if opp else RawJobPosting(id=job_id, platform=PlatformType.CUSTOM, title=f"Contract Solution #{job_id}", description="")
                score = opp.decision.overall_score if opp else 90.0

                html_doc = HTMLBlueprintBuilder.build(
                    job=job,
                    proposal=proposal,
                    inspection=None,
                    overall_score=score
                )

                return await self.client.send_document(
                    chat_id=chat_id,
                    file_bytes=html_doc.encode("utf-8"),
                    filename=f"Genesis_Blueprint_{job_id}.html",
                    caption=f"⚡ <b>Genesis Solution Blueprint: #{job_id}</b>\n"
                            f"<i>Includes 3-phase milestone roadmap and full untruncated AST prototype. Tap to view in browser.</i>"
                )

            elif action == "ground_truth":
                diagnosis = proposal.sentence_1_pain_diagnosis if proposal else "Standard description context."
                return await self.client.answer_callback_query(callback_query_id, text=f"🎯 Ground Truth: {diagnosis[:150]}", show_alert=True)

        return await self.client.answer_callback_query(callback_query_id, text="Action processed.")

    async def handle_text_message(self, chat_id: str, text: str, username: str = "") -> Optional[Dict[str, Any]]:
        """Handles incoming text, commands, or custom keyword input."""
        clean_text = text.strip()
        profile = self.user_store.get_or_create(chat_id, username)

        # Commands
        if clean_text == "/start":
            return await self.handle_start(chat_id, username)

        elif clean_text == "/status":
            summary = self.get_status_summary(chat_id)
            return await self.client.send_message(chat_id=chat_id, text=summary)

        elif clean_text == "/search":
            return await self.execute_user_search(chat_id)

        elif clean_text == "/criteria" or clean_text == "/settings":
            return await self.handle_start(chat_id, username)

        # Custom Keyword Input during wizard
        if profile.step == "AWAITING_CUSTOM_KEYWORD":
            profile.custom_keyword = clean_text
            profile.skill_keywords = [k.strip().lower() for k in clean_text.split(",") if k.strip()]
            profile.step = "SELECTING_PLATFORM"
            self.user_store.update_profile(profile)

            msg_text, kb = OnboardingWizard.step_2_platforms(f"Custom: '{clean_text}'")
            return await self.client.send_message(chat_id=chat_id, text=msg_text, reply_markup=kb)

        return None

    def get_status_summary(self, target: Any = None) -> str:
        """Returns radar status in 100% English. Supports both user_id string and criteria object."""
        if isinstance(target, UserFilterCriteria):
            criteria = target
            return (
                f"📊 <b>Haiox Project Scout Mission Control</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 <b>Processed Opportunities:</b> {len(self.stored_proposals)}\n"
                f"✅ <b>Approved:</b> {len(self.approved_jobs)} | ❌ <b>Dismissed:</b> {len(self.dismissed_jobs)}\n"
                f"⚙️ <b>Active Filter Floor:</b> ${criteria.min_price} USD\n"
                f"🔍 <b>Required Keywords:</b> {', '.join(criteria.required_keywords) or 'None'}\n"
                f"🛡️ <b>Verified Clients Only:</b> {'Yes' if criteria.payment_verified_only else 'No'}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Status: 🟢 OPERATIONAL"
            )

        chat_id = str(target or self.admin_chat_id)
        profile = self.user_store.get_or_create(chat_id)
        skill_info = SKILL_TAXONOMY.get(profile.skill_category, {})
        skill_name = profile.custom_keyword or skill_info.get("label", profile.skill_category.upper())
        mode_str = "🔔 Continuous Real-Time Alerts" if profile.delivery_mode == "realtime" else "🔍 On-Demand Query Only"

        return (
            f"📊 <b>Haiox Project Scout - Personal Radar Status</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Operator ID:</b> <code>{chat_id}</code>\n"
            f"🎯 <b>Active Skill:</b> {skill_name}\n"
            f"🔍 <b>Tracking Keywords:</b> {', '.join(profile.skill_keywords)}\n"
            f"💰 <b>Budget Floor:</b> ${profile.min_budget:,.0f} USD\n"
            f"📡 <b>Delivery Mode:</b> {mode_str}\n"
            f"✅ <b>Approved:</b> {len(self.approved_jobs)} | ❌ <b>Dismissed:</b> {len(self.dismissed_jobs)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Status: 🟢 OPERATIONAL\n"
            f"<i>Type /settings to reconfigure your skills or budget anytime.</i>"
        )

    async def dispatch_opportunity(
        self,
        job: RawJobPosting,
        proposal: SynthesizedProposal,
        score: float,
        target_chat_id: Optional[str] = None
    ) -> bool:
        """Dispatches synthesized proposal and blueprint alert card to specific user."""
        self.stored_proposals[job.id] = proposal
        keyboard = self.build_opportunity_keyboard(job)
        dest_chat = str(target_chat_id or self.admin_chat_id)

        try:
            res = await self.client.send_message(
                chat_id=dest_chat,
                text=proposal.telegram_card_markdown,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            return res.get("ok", False)
        except Exception as e:
            print(f"[MissionControl] Error dispatching opportunity {job.id} to {dest_chat}: {e}")
            return False

    async def execute_user_search(self, chat_id: str) -> Dict[str, Any]:
        """Performs sub-millisecond query on OpportunityCache and displays an interactive carousel deal deck."""
        from core.job_cache import GLOBAL_OPPORTUNITY_CACHE
        profile = self.user_store.get_or_create(chat_id)

        matches, is_fallback, notice = GLOBAL_OPPORTUNITY_CACHE.search_with_smart_fallback(
            keywords=profile.skill_keywords,
            min_budget=profile.min_budget,
            platforms=profile.platforms,
            limit=5
        )

        active_matches = [m for m in matches if m.job.id not in self.dismissed_jobs]
        if not active_matches and matches:
            active_matches = matches

        if not active_matches:
            return await self.client.send_message(
                chat_id=chat_id,
                text="🔍 <b>Live Opportunity Radar:</b>\n"
                     "<i>Radar cache is currently warming up with live feeds. Please try again in a few moments or type /search.</i>"
            )

        self.user_search_decks[str(chat_id)] = {
            "opportunities": active_matches,
            "notice": notice,
            "is_fallback": is_fallback
        }

        # Cache proposals for instant one-tap copy & code delivery
        for opp in active_matches:
            self.stored_proposals[opp.job.id] = opp.proposal

        card_text, card_kb = self.render_deck_card(active_matches[0], 0, len(active_matches), notice)
        return await self.client.send_message(
            chat_id=chat_id,
            text=card_text,
            parse_mode="HTML",
            reply_markup=card_kb,
            disable_web_page_preview=True
        )
