"""
Haiox Project Scout - Async Telegram Bot Client
Module: bot/telegram_client.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import httpx


@dataclass
class InlineKeyboardButton:
    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"text": self.text}
        if self.callback_data:
            d["callback_data"] = self.callback_data
        if self.url:
            d["url"] = self.url
        return d


@dataclass
class InlineKeyboardMarkup:
    inline_keyboard: List[List[InlineKeyboardButton]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inline_keyboard": [
                [btn.to_dict() for btn in row]
                for row in self.inline_keyboard
            ]
        }


class TelegramBotClient:
    """
    Lightweight, asynchronous Telegram Bot API client using httpx.
    Supports dry-run / mock simulation for testing and offline verification.
    """

    def __init__(
        self,
        bot_token: str = "",
        dry_run: bool = False,
        timeout_seconds: float = 10.0
    ):
        self.bot_token = bot_token.strip()
        self.dry_run = dry_run or not bool(self.bot_token)
        self.timeout = timeout_seconds
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else ""
        self.sent_messages: List[Dict[str, Any]] = []
        self.edited_messages: List[Dict[str, Any]] = []

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        disable_web_page_preview: bool = True
    ) -> Dict[str, Any]:
        """Dispatches an HTML/Markdown formatted message with optional inline keyboard."""
        payload: Dict[str, Any] = {
            "chat_id": str(chat_id),
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup.to_dict()

        if self.dry_run:
            self.sent_messages.append(payload)
            return {"ok": True, "result": {"message_id": len(self.sent_messages), "dry_run": True}}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/sendMessage", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def edit_message_text(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        disable_web_page_preview: bool = True
    ) -> Dict[str, Any]:
        """Edits an existing message in-place for seamless wizard transitions."""
        payload: Dict[str, Any] = {
            "chat_id": str(chat_id),
            "message_id": int(message_id),
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup.to_dict()

        if self.dry_run:
            self.edited_messages.append(payload)
            return {"ok": True, "result": {"message_id": message_id, "dry_run": True}}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/editMessageText", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> Dict[str, Any]:
        """Acknowledges a user interaction on an inline keyboard button."""
        payload: Dict[str, Any] = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert,
        }
        if text:
            payload["text"] = text

        if self.dry_run:
            return {"ok": True, "result": True, "dry_run": True}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/answerCallbackQuery", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def send_document(
        self,
        chat_id: str,
        file_bytes: bytes,
        filename: str,
        caption: str = "",
        parse_mode: str = "HTML"
    ) -> Dict[str, Any]:
        """Dispatches a standalone document (e.g. HTML solution report) to Telegram."""
        if self.dry_run:
            payload = {"chat_id": str(chat_id), "filename": filename, "caption": caption, "size": len(file_bytes)}
            self.sent_messages.append(payload)
            return {"ok": True, "result": {"message_id": len(self.sent_messages), "dry_run": True}}

        async with httpx.AsyncClient(timeout=self.timeout + 10.0) as client:
            files = {"document": (filename, file_bytes, "text/html")}
            data = {"chat_id": str(chat_id), "caption": caption, "parse_mode": parse_mode}
            resp = await client.post(f"{self.base_url}/sendDocument", data=data, files=files)
            resp.raise_for_status()
            return resp.json()

    async def get_updates(self, offset: Optional[int] = None, limit: int = 10, timeout: int = 0) -> List[Dict[str, Any]]:
        """Retrieves inbound bot updates (commands and callback queries)."""
        if self.dry_run:
            return []

        params: Dict[str, Any] = {"limit": limit, "timeout": timeout}
        if offset is not None:
            params["offset"] = offset

        async with httpx.AsyncClient(timeout=self.timeout + timeout) as client:
            resp = await client.get(f"{self.base_url}/getUpdates", params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", [])
