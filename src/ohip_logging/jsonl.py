"""
JSONL event logging utilities for IX-HapticSight.

This module provides a simple, backend-agnostic structured event log format
based on newline-delimited JSON. The format is intended to support:

- runtime audit trails
- replay inputs
- benchmark artifacts
- deterministic debugging bundles

Design goals:
- append-friendly
- human-inspectable
- stable enough for replay and tests
- no hidden console-only behavior
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator, Optional

from .events import EventRecord


class EventLogWriter:
    """
    Append-oriented JSONL writer for structured event records.

    Each line is one serialized EventRecord dictionary.

    This class intentionally avoids buffering large in-memory structures.
    It is meant to be simple and predictable for local runtime logs,
    benchmark outputs, and replay artifacts.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def ensure_parent_dir(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: EventRecord) -> None:
        """
        Append a single event record to the log.
        """
        self.ensure_parent_dir()
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(_encode_event(event))
            handle.write("\n")

    def append_many(self, events: Iterable[EventRecord]) -> int:
        """
        Append multiple events and return the number written.
        """
        self.ensure_parent_dir()
        written = 0
        with self._path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(_encode_event(event))
                handle.write("\n")
                written += 1
        return written

    def exists(self) -> bool:
        return self._path.exists()

    def read_all(self) -> list[EventRecord]:
        return list(iter_event_log(self._path))

    def clear(self) -> None:
        """
        Remove all content from the log file, preserving the file path.
        """
        self.ensure_parent_dir()
        self._path.write_text("", encoding="utf-8")


def iter_event_log(path: str | Path) -> Iterator[EventRecord]:
    """
    Iterate over a JSONL event log.

    Blank lines are ignored.
    """
    log_path = Path(path)
    if not log_path.exists():
        return iter(())
    return _iter_event_lines(log_path)


def load_event_log(path: str | Path) -> list[EventRecord]:
    """
    Load all events from a JSONL event log.
    """
    return list(iter_event_log(path))


def write_event_log(path: str | Path, events: Iterable[EventRecord]) -> int:
    """
    Overwrite a log file with exactly the provided event sequence.
    Returns the number of written events.
    """
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with log_path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(_encode_event(event))
            handle.write("\n")
            written += 1
    return written


def tail_event_log(path: str | Path, limit: int = 20) -> list[EventRecord]:
    """
    Return the last N events from a log.

    This implementation reads the full file for simplicity and correctness.
    That is acceptable for the small-to-moderate artifact sizes expected in
    this repository stage.
    """
    if limit <= 0:
        return []
    events = load_event_log(path)
    return events[-limit:]


def last_event(path: str | Path) -> Optional[EventRecord]:
    """
    Return the last event in a log or None if the file is missing or empty.
    """
    events = tail_event_log(path, limit=1)
    return events[0] if events else None


def _iter_event_lines(path: Path) -> Iterator[EventRecord]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON in event log at line {line_number}: {path}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"event log line {line_number} is not a JSON object: {path}")
            yield EventRecord.from_dict(payload)


def _encode_event(event: EventRecord) -> str:
    return json.dumps(
        event.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


__all__ = [
    "EventLogWriter",
    "iter_event_log",
    "load_event_log",
    "write_event_log",
    "tail_event_log",
    "last_event",
]
