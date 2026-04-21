"""
In-memory runtime session store for IX-HapticSight.

This module provides a small, explicit registry for InteractionSession objects.
It is intentionally simple and backend-agnostic so it can be reused by:

- local runtime coordinators
- future ROS 2 wrappers
- replay tools
- benchmark harnesses
- integration tests

The store does not replace a real database or distributed runtime state system.
Its purpose is to keep session ownership visible and deterministic during the
repository's runtime buildout phase.
"""

from __future__ import annotations

from dataclasses import replace
from threading import RLock
from typing import Dict, Iterable, Optional

from .state import InteractionSession


class SessionStore:
    """
    Thread-safe in-memory registry for interaction sessions.

    Design goals:
    - explicit session lifecycle
    - no hidden globals
    - safe-by-default duplicate handling
    - snapshots returned to callers to reduce accidental shared mutation
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: Dict[str, InteractionSession] = {}

    def exists(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._sessions

    def create(self, session: InteractionSession, *, overwrite: bool = False) -> InteractionSession:
        """
        Insert a new session.

        By default, duplicate session IDs are rejected to avoid silent state
        replacement. Set overwrite=True only when the caller has an explicit
        reason to replace existing state.
        """
        with self._lock:
            if not overwrite and session.session_id in self._sessions:
                raise ValueError(f"session already exists: {session.session_id}")
            self._sessions[session.session_id] = replace(session)
            return replace(self._sessions[session.session_id])

    def get(self, session_id: str) -> Optional[InteractionSession]:
        """
        Return a detached snapshot of the session, or None if not found.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            return replace(session) if session is not None else None

    def require(self, session_id: str) -> InteractionSession:
        """
        Return a detached snapshot of the session or raise KeyError.
        """
        session = self.get(session_id)
        if session is None:
            raise KeyError(f"unknown session_id: {session_id}")
        return session

    def update(self, session: InteractionSession) -> InteractionSession:
        """
        Replace an existing session with a new snapshot.

        This method is explicit on purpose. Callers should construct the next
        session state and then commit it rather than mutating shared global
        state through hidden references.
        """
        with self._lock:
            if session.session_id not in self._sessions:
                raise KeyError(f"unknown session_id: {session.session_id}")
            self._sessions[session.session_id] = replace(session)
            return replace(self._sessions[session.session_id])

    def upsert(self, session: InteractionSession) -> InteractionSession:
        """
        Insert or replace a session snapshot.
        """
        with self._lock:
            self._sessions[session.session_id] = replace(session)
            return replace(self._sessions[session.session_id])

    def delete(self, session_id: str) -> bool:
        """
        Remove a session if present. Returns True when something was deleted.
        """
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()

    def list_ids(self) -> list[str]:
        with self._lock:
            return sorted(self._sessions.keys())

    def list_sessions(self) -> list[InteractionSession]:
        with self._lock:
            return [replace(self._sessions[sid]) for sid in sorted(self._sessions.keys())]

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def bulk_upsert(self, sessions: Iterable[InteractionSession]) -> int:
        """
        Upsert multiple sessions and return the number written.
        """
        written = 0
        with self._lock:
            for session in sessions:
                self._sessions[session.session_id] = replace(session)
                written += 1
        return written


__all__ = [
    "SessionStore",
]
