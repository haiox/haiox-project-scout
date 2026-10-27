"""
Haiox Project Scout - Multi-Tenant User Profile & Preference Store
Module: bot/user_state.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

USER_PROFILES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "user_profiles.json"
)

# Skill Taxonomy Mapping: maps category identifiers to search keyword lists
SKILL_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "python": {
        "label": "🐍 Python, Scraping & Bots",
        "keywords": ["python", "scraper", "scraping", "crawler", "bot", "automation", "fastapi"],
    },
    "ai": {
        "label": "🤖 AI, LLMs & Machine Learning",
        "keywords": ["ai", "llm", "openai", "langchain", "machine learning", "deep learning", "agent"],
    },
    "web": {
        "label": "🌐 Web & Fullstack",
        "keywords": ["react", "nextjs", "vue", "nodejs", "django", "fullstack", "api", "shopify"],
    },
    "mobile": {
        "label": "📱 Mobile Apps",
        "keywords": ["flutter", "react native", "ios", "android", "swift", "kotlin"],
    },
    "data": {
        "label": "📊 Data & Analytics",
        "keywords": ["excel", "data analysis", "sql", "powerbi", "cleaning", "data entry"],
    },
}


@dataclass
class UserProfile:
    """Represents an individual Telegram user's scout configuration and preferences."""
    user_id: str
    username: str = ""
    step: str = "NEW"  # NEW, SELECTING_PLATFORM, SELECTING_BUDGET, SELECTING_MODE, AWAITING_CUSTOM_KEYWORD, READY
    skill_category: str = "python"
    skill_keywords: List[str] = field(default_factory=lambda: ["python", "scraper"])
    custom_keyword: Optional[str] = None
    platforms: List[str] = field(default_factory=lambda: ["all"])
    min_budget: float = 0.0
    delivery_mode: str = "realtime"  # "realtime" or "ondemand"
    enable_genesis_ai: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        return cls(**data)


class UserStateStore:
    """Thread-safe persistent storage for Telegram bot users."""

    def __init__(self, storage_path: str = USER_PROFILES_FILE):
        self.storage_path = storage_path
        self._profiles: Dict[str, UserProfile] = {}
        self.load()

    def load(self):
        """Loads profiles from JSON storage if exists."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._profiles = {
                        uid: UserProfile.from_dict(prof)
                        for uid, prof in data.items()
                    }
            except Exception as e:
                print(f"[UserStateStore] Error loading user profiles: {e}")
                self._profiles = {}

    def save(self):
        """Persists all profiles atomically to disk."""
        try:
            temp_path = f"{self.storage_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(
                    {uid: p.to_dict() for uid, p in self._profiles.items()},
                    f,
                    indent=2
                )
            if os.path.exists(self.storage_path):
                os.remove(self.storage_path)
            os.rename(temp_path, self.storage_path)
        except Exception as e:
            print(f"[UserStateStore] Error saving user profiles: {e}")

    def get_or_create(self, user_id: str, username: str = "") -> UserProfile:
        uid = str(user_id)
        if uid not in self._profiles:
            self._profiles[uid] = UserProfile(user_id=uid, username=username)
            self.save()
        else:
            if username and self._profiles[uid].username != username:
                self._profiles[uid].username = username
                self.save()
        return self._profiles[uid]

    def update_profile(self, profile: UserProfile):
        profile.updated_at = time.time()
        self._profiles[str(profile.user_id)] = profile
        self.save()

    def get_all_realtime_users(self) -> List[UserProfile]:
        return [
            p for p in self._profiles.values()
            if p.step == "READY" and p.delivery_mode == "realtime"
        ]
