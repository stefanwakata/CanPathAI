"""Conversation memory with TTL, keyed by session id.

Messages live in process memory; the profile is also persisted to PostgreSQL
(user_profiles table) so it survives backend restarts. For multi-replica
deployments swap the in-process part for Redis.
"""
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from threading import Lock

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _db_load_profile(session_id: str) -> dict | None:
    try:
        from app.core.db import db_session
        from app.models.tables import UserProfileRow

        with db_session() as s:
            row = s.get(UserProfileRow, session_id)
            return json.loads(row.profile_json) if row else None
    except Exception as exc:
        logger.warning("Could not load profile from DB: %s", exc)
        return None


def _db_save_profile(session_id: str, profile: dict) -> None:
    try:
        from datetime import datetime

        from app.core.db import db_session
        from app.models.tables import UserProfileRow

        with db_session() as s:
            row = s.get(UserProfileRow, session_id)
            if row is None:
                s.add(UserProfileRow(session_id=session_id,
                                     profile_json=json.dumps(profile),
                                     updated_at=datetime.utcnow()))
            else:
                row.profile_json = json.dumps(profile)
                row.updated_at = datetime.utcnow()
    except Exception as exc:
        logger.warning("Could not persist profile to DB: %s", exc)


@dataclass
class SessionState:
    messages: list[dict] = field(default_factory=list)  # {"role","content"}
    profile: dict | None = None
    last_seen: float = field(default_factory=time.time)


class MemoryStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._lock = Lock()

    def _prune(self) -> None:
        ttl = get_settings().session_ttl_minutes * 60
        now = time.time()
        stale = [k for k, v in self._sessions.items() if now - v.last_seen > ttl]
        for k in stale:
            del self._sessions[k]

    def get_or_create(self, session_id: str | None) -> tuple[str, SessionState]:
        with self._lock:
            self._prune()
            sid = session_id or uuid.uuid4().hex
            created = sid not in self._sessions
            state = self._sessions.setdefault(sid, SessionState())
            if created and session_id is not None and state.profile is None:
                state.profile = _db_load_profile(sid)  # restore after restart
            state.last_seen = time.time()
            return sid, state

    def append(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            state = self._sessions.setdefault(session_id, SessionState())
            state.messages.append({"role": role, "content": content})
            limit = get_settings().max_history_messages
            if len(state.messages) > limit:
                state.messages = state.messages[-limit:]
            state.last_seen = time.time()

    def set_profile(self, session_id: str, profile: dict) -> None:
        with self._lock:
            state = self._sessions.setdefault(session_id, SessionState())
            if state.profile == profile:
                state.last_seen = time.time()
                return
            state.profile = profile
            state.last_seen = time.time()
        _db_save_profile(session_id, profile)


memory_store = MemoryStore()
