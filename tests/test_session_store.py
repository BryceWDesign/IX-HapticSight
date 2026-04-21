"""
IX-HapticSight — Tests for the in-memory runtime session store.

These tests verify the basic session-lifecycle guarantees for the
backend-agnostic SessionStore introduced under `src/ohip_runtime/`.
"""

import os
import sys

# Make both `ohip` and `ohip_runtime` importable without packaging
sys.path.insert(0, os.path.abspath("src"))

from ohip.schemas import SafetyLevel  # noqa: E402
from ohip_runtime.session_store import SessionStore  # noqa: E402
from ohip_runtime.state import (  # noqa: E402
    ExecutionState,
    InteractionSession,
    InteractionState,
)


def make_session(session_id: str) -> InteractionSession:
    return InteractionSession(
        session_id=session_id,
        subject_id=f"{session_id}-subject",
        interaction_state=InteractionState.IDLE,
        execution_state=ExecutionState.IDLE,
        safety_level=SafetyLevel.GREEN,
    )


def test_create_and_get_session_snapshot():
    store = SessionStore()
    created = store.create(make_session("s-1"))

    assert created.session_id == "s-1"
    assert store.exists("s-1") is True
    assert store.count() == 1

    loaded = store.get("s-1")
    assert loaded is not None
    assert loaded.session_id == "s-1"
    assert loaded.subject_id == "s-1-subject"


def test_duplicate_create_raises_without_overwrite():
    store = SessionStore()
    store.create(make_session("s-2"))

    try:
        store.create(make_session("s-2"))
        raised = False
    except ValueError:
        raised = True

    assert raised is True
    assert store.count() == 1


def test_create_with_overwrite_replaces_existing():
    store = SessionStore()

    original = make_session("s-3")
    store.create(original)

    replacement = make_session("s-3")
    replacement.subject_id = "updated-subject"
    replacement.interaction_state = InteractionState.VERIFY

    store.create(replacement, overwrite=True)

    loaded = store.require("s-3")
    assert loaded.subject_id == "updated-subject"
    assert loaded.interaction_state == InteractionState.VERIFY


def test_get_returns_detached_snapshot():
    store = SessionStore()
    store.create(make_session("s-4"))

    loaded = store.require("s-4")
    loaded.subject_id = "mutated-locally"
    loaded.interaction_state = InteractionState.CONTACT

    fresh = store.require("s-4")
    assert fresh.subject_id == "s-4-subject"
    assert fresh.interaction_state == InteractionState.IDLE


def test_update_replaces_existing_snapshot():
    store = SessionStore()
    session = make_session("s-5")
    store.create(session)

    updated = store.require("s-5")
    updated.execution_state = ExecutionState.READY
    updated.interaction_state = InteractionState.APPROACH

    store.update(updated)

    loaded = store.require("s-5")
    assert loaded.execution_state == ExecutionState.READY
    assert loaded.interaction_state == InteractionState.APPROACH


def test_update_unknown_session_raises_key_error():
    store = SessionStore()

    try:
        store.update(make_session("missing"))
        raised = False
    except KeyError:
        raised = True

    assert raised is True


def test_upsert_and_bulk_upsert_work():
    store = SessionStore()

    assert store.count() == 0

    store.upsert(make_session("s-6"))
    assert store.count() == 1

    written = store.bulk_upsert(
        [
            make_session("s-7"),
            make_session("s-8"),
        ]
    )
    assert written == 2
    assert store.count() == 3
    assert store.list_ids() == ["s-6", "s-7", "s-8"]


def test_delete_and_clear():
    store = SessionStore()
    store.bulk_upsert(
        [
            make_session("s-9"),
            make_session("s-10"),
        ]
    )

    assert store.count() == 2

    deleted = store.delete("s-9")
    assert deleted is True
    assert store.exists("s-9") is False
    assert store.count() == 1

    store.clear()
    assert store.count() == 0
    assert store.list_sessions() == []
