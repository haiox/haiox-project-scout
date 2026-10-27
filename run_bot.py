"""
Haiox Project Scout - Live Interactive & Continuous Ingestion Service Runner
Module: run_bot.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import asyncio
import os
import sys
from pathlib import Path

# Ensure root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from bot.telegram_client import TelegramBotClient
from bot.user_state import UserStateStore
from bot.mission_control import MissionControl
from daemon import ScoutAutonomousDaemon
from core.job_cache import GLOBAL_OPPORTUNITY_CACHE


async def listener_loop(mission_control: MissionControl, client: TelegramBotClient):
    """Sub-second listener for user interactions (/start, wizard callbacks, /search)."""
    print("[Listener] Interactive Telegram event listener active.")
    offset = None
    while True:
        try:
            updates = await client.get_updates(offset=offset, timeout=10)
            for u in updates:
                offset = u.get("update_id", 0) + 1

                # Handle Text Messages
                if "message" in u:
                    msg = u["message"]
                    chat_id = str(msg.get("chat", {}).get("id"))
                    text = msg.get("text", "")
                    username = msg.get("from", {}).get("username", "")
                    if text:
                        await mission_control.handle_text_message(chat_id=chat_id, text=text, username=username)

                # Handle Inline Button Clicks
                elif "callback_query" in u:
                    cb = u["callback_query"]
                    cb_id = cb.get("id")
                    data = cb.get("data", "")
                    msg = cb.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id"))
                    message_id = msg.get("message_id")

                    if data and message_id:
                        await mission_control.handle_callback_query(
                            callback_query_id=cb_id,
                            chat_id=chat_id,
                            message_id=message_id,
                            data=data
                        )

        except asyncio.CancelledError:
            break
        except Exception as e:
            await asyncio.sleep(2)


async def background_scout_loop(daemon: ScoutAutonomousDaemon):
    """Background engine keeping the in-memory opportunity cache hot and auto-dispatching."""
    print("[ScoutDaemon] Background ingestion daemon started.")
    await asyncio.sleep(1)  # Brief warm-up

    while True:
        try:
            res = await daemon.run_single_cycle()
            print(f"[ScoutDaemon] Cycle {res['cycle']} finished in {res['duration_seconds']}s. "
                  f"Ingested: {res['total_ingested']} | Hot Cache: {GLOBAL_OPPORTUNITY_CACHE.count()} items.")
            await asyncio.sleep(daemon.poll_interval)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[ScoutDaemon] Ingestion cycle error: {e}. Retrying in 10s...")
            await asyncio.sleep(10)


async def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("[Service] ERROR: TELEGRAM_BOT_TOKEN is not configured.")
        return

    client = TelegramBotClient(bot_token=token)
    user_store = UserStateStore()
    mission_control = MissionControl(bot_client=client, user_store=user_store)
    daemon = ScoutAutonomousDaemon(mission_control=mission_control)

    print("[Service] Starting Haiox Project Scout Unified Dual-Engine (Listener + Scout)...")

    # Run both the interactive user listener and background ingestion concurrently
    await asyncio.gather(
        listener_loop(mission_control, client),
        background_scout_loop(daemon)
    )


if __name__ == "__main__":
    asyncio.run(main())
