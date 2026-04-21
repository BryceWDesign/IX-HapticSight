"""
Replay helpers for IX-HapticSight structured event logs.

This module provides a small, backend-agnostic replay layer built on top of the
JSONL event format defined in `ohip_logging.jsonl`.

Design goals:
- deterministic event ordering
- easy filtering by session, request, or event kind
- no confusion between live runtime state and replay artifacts
- lightweight enough for tests, local debugging, and future benchmark runners
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator, Optional, Sequence

from .events import EventKind, EventRecord
from .jsonl import load_event_log


ReplayPredicate = Callable[[EventRecord], bool]


@dataclass(frozen=True)
class ReplayCursor:
    """
    Lightweight position marker for replay iteration.
    """

    index: int = 0


@dataclass(frozen=True)
class ReplaySlice:
    """
    A filtered replayable slice of events.

    This is useful for:
    - one session
    - one request
    - one benchmark marker range
    - one event kind subset
    """

    name: str
    events: tuple[EventRecord, ...]

    def __len__(self) -> int:
        return len(self.events)

    def first(self) -> Optional[EventRecord]:
        return self.events[0] if self.events else None

    def last(self) -> Optional[EventRecord]:
        return self.events[-1] if self.events else None

    def kinds(self) -> list[str]:
        seen: list[str] = []
        for event in self.events:
            value = event.kind.value
            if value not in seen:
                seen.append(value)
        return seen

    def session_ids(self) -> list[str]:
        seen: list[str] = []
        for event in self.events:
            if event.session_id and event.session_id not in seen:
                seen.append(event.session_id)
        return seen

    def request_ids(self) -> list[str]:
        seen: list[str] = []
        for event in self.events:
            if event.request_id and event.request_id not in seen:
                seen.append(event.request_id)
        return seen

    def to_list(self) -> list[EventRecord]:
        return list(self.events)


class EventReplay:
    """
    Deterministic in-memory replay view of a structured event sequence.

    This class does not simulate physics or command execution. Its purpose is to
    replay the event trail itself in a predictable way for:
    - audit
    - debugging
    - benchmark comparisons
    - integration tests
    """

    def __init__(self, events: Sequence[EventRecord], *, source_label: str = "") -> None:
        self._events: tuple[EventRecord, ...] = tuple(events)
        self._source_label = source_label

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "EventReplay":
        replay_path = Path(path)
        return cls(load_event_log(replay_path), source_label=str(replay_path))

    @property
    def source_label(self) -> str:
        return self._source_label

    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self) -> Iterator[EventRecord]:
        return iter(self._events)

    def all(self) -> list[EventRecord]:
        return list(self._events)

    def first(self) -> Optional[EventRecord]:
        return self._events[0] if self._events else None

    def last(self) -> Optional[EventRecord]:
        return self._events[-1] if self._events else None

    def at(self, index: int) -> EventRecord:
        return self._events[index]

    def next_from(self, cursor: ReplayCursor) -> tuple[Optional[EventRecord], ReplayCursor]:
        """
        Return the next event and the advanced cursor.

        If the cursor is at or beyond the end, returns (None, same cursor).
        """
        if cursor.index < 0:
            raise ValueError("cursor index must be non-negative")
        if cursor.index >= len(self._events):
            return None, cursor
        event = self._events[cursor.index]
        return event, ReplayCursor(index=cursor.index + 1)

    def filter(self, predicate: ReplayPredicate, *, name: str = "filtered") -> ReplaySlice:
        return ReplaySlice(
            name=name,
            events=tuple(event for event in self._events if predicate(event)),
        )

    def by_session(self, session_id: str) -> ReplaySlice:
        return self.filter(
            lambda event: event.session_id == session_id,
            name=f"session:{session_id}",
        )

    def by_request(self, request_id: str) -> ReplaySlice:
        prefix = f"{request_id}:"
        return self.filter(
            lambda event: event.request_id == request_id or event.event_id.startswith(prefix),
            name=f"request:{request_id}",
        )

    def by_kind(self, *kinds: EventKind | str) -> ReplaySlice:
        normalized = {
            kind.value if isinstance(kind, EventKind) else str(kind)
            for kind in kinds
        }
        return self.filter(
            lambda event: event.kind.value in normalized,
            name="kind:" + ",".join(sorted(normalized)),
        )

    def between_event_ids(
        self,
        start_event_id: str,
        end_event_id: str,
        *,
        include_end: bool = True,
        name: str = "",
    ) -> ReplaySlice:
        """
        Return the contiguous event slice between two event IDs.

        Raises ValueError if either boundary is missing or if the order is invalid.
        """
        start_index = None
        end_index = None

        for idx, event in enumerate(self._events):
            if start_index is None and event.event_id == start_event_id:
                start_index = idx
            if event.event_id == end_event_id:
                end_index = idx
                if start_index is not None:
                    break

        if start_index is None:
            raise ValueError(f"unknown start_event_id: {start_event_id}")
        if end_index is None:
            raise ValueError(f"unknown end_event_id: {end_event_id}")
        if end_index < start_index:
            raise ValueError("end_event_id appears before start_event_id")

        stop = end_index + 1 if include_end else end_index
        label = name or f"range:{start_event_id}..{end_event_id}"
        return ReplaySlice(
            name=label,
            events=self._events[start_index:stop],
        )

    def benchmark_markers(self) -> ReplaySlice:
        return self.by_kind(EventKind.BENCHMARK_MARKER)

    def replay_markers(self) -> ReplaySlice:
        return self.by_kind(EventKind.REPLAY_MARKER)

    def session_ids(self) -> list[str]:
        seen: list[str] = []
        for event in self._events:
            if event.session_id and event.session_id not in seen:
                seen.append(event.session_id)
        return seen

    def request_ids(self) -> list[str]:
        seen: list[str] = []
        for event in self._events:
            if event.request_id and event.request_id not in seen:
                seen.append(event.request_id)
        return seen

    def summary(self) -> dict[str, object]:
        kind_counts: dict[str, int] = {}
        for event in self._events:
            key = event.kind.value
            kind_counts[key] = kind_counts.get(key, 0) + 1

        return {
            "source_label": self._source_label,
            "event_count": len(self._events),
            "session_ids": self.session_ids(),
            "request_ids": self.request_ids(),
            "kind_counts": kind_counts,
            "first_event_id": self.first().event_id if self.first() else None,
            "last_event_id": self.last().event_id if self.last() else None,
        }


def merge_replay_streams(
    streams: Iterable[Sequence[EventRecord]],
    *,
    source_label: str = "merged",
) -> EventReplay:
    """
    Merge multiple already-ordered event sequences into one replay stream.

    Ordering rule:
    - primary sort by created_at_utc_s
    - secondary sort by event_id for deterministic tie-breaking
    """
    merged: list[EventRecord] = []
    for stream in streams:
        merged.extend(stream)

    merged.sort(key=lambda event: (float(event.created_at_utc_s), event.event_id))
    return EventReplay(merged, source_label=source_label)


__all__ = [
    "ReplayCursor",
    "ReplaySlice",
    "EventReplay",
    "merge_replay_streams",
]
