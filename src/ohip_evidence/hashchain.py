"""Tamper-evident evidence chain for IX-HapticSight runtime records."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from time import time
from typing import Any, Iterable

GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class ChainedEvidenceRecord:
    sequence: int
    timestamp_s: float
    kind: str
    payload: dict[str, Any]
    previous_hash: str
    record_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical_bytes(*, sequence: int, timestamp_s: float, kind: str, payload: dict[str, Any], previous_hash: str) -> bytes:
    body = {
        "sequence": int(sequence),
        "timestamp_s": float(timestamp_s),
        "kind": str(kind),
        "payload": payload,
        "previous_hash": str(previous_hash),
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class EvidenceChain:
    def __init__(self) -> None:
        self._records: list[ChainedEvidenceRecord] = []

    @property
    def records(self) -> tuple[ChainedEvidenceRecord, ...]:
        return tuple(self._records)

    def append(self, kind: str, payload: dict[str, Any], *, timestamp_s: float | None = None) -> ChainedEvidenceRecord:
        sequence = len(self._records)
        previous_hash = self._records[-1].record_hash if self._records else GENESIS_HASH
        ts = time() if timestamp_s is None else float(timestamp_s)
        digest = hashlib.sha256(
            _canonical_bytes(
                sequence=sequence,
                timestamp_s=ts,
                kind=kind,
                payload=payload,
                previous_hash=previous_hash,
            )
        ).hexdigest()
        record = ChainedEvidenceRecord(sequence, ts, str(kind), dict(payload), previous_hash, digest)
        self._records.append(record)
        return record

    def verify(self) -> tuple[bool, str]:
        return verify_records(self._records)

    def to_jsonl(self) -> str:
        return "".join(json.dumps(r.to_dict(), sort_keys=True) + "\n" for r in self._records)


def verify_records(records: Iterable[ChainedEvidenceRecord]) -> tuple[bool, str]:
    previous = GENESIS_HASH
    for expected_sequence, record in enumerate(records):
        if record.sequence != expected_sequence:
            return False, f"sequence_mismatch:{expected_sequence}"
        if record.previous_hash != previous:
            return False, f"previous_hash_mismatch:{expected_sequence}"
        expected = hashlib.sha256(
            _canonical_bytes(
                sequence=record.sequence,
                timestamp_s=record.timestamp_s,
                kind=record.kind,
                payload=record.payload,
                previous_hash=record.previous_hash,
            )
        ).hexdigest()
        if expected != record.record_hash:
            return False, f"record_hash_mismatch:{expected_sequence}"
        previous = record.record_hash
    return True, "ok"
