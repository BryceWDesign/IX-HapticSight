"""Portable evidence-bundle writer and verifier."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .hashchain import ChainedEvidenceRecord, verify_records


@dataclass(frozen=True)
class EvidenceBundleManifest:
    schema_version: str
    record_count: int
    chain_head_sha256: str
    records_sha256: str
    provenance: dict[str, Any]


class EvidenceBundle:
    @staticmethod
    def write(directory: str | Path, records: tuple[ChainedEvidenceRecord, ...], *, provenance: dict[str, Any]) -> EvidenceBundleManifest:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        ok, reason = verify_records(records)
        if not ok:
            raise ValueError(f"cannot bundle invalid evidence chain: {reason}")
        records_text = "".join(json.dumps(r.to_dict(), sort_keys=True) + "\n" for r in records)
        records_path = path / "records.jsonl"
        records_path.write_text(records_text, encoding="utf-8")
        records_hash = hashlib.sha256(records_text.encode("utf-8")).hexdigest()
        head = records[-1].record_hash if records else "0" * 64
        manifest = EvidenceBundleManifest(
            schema_version="ixhs-evidence-v1",
            record_count=len(records),
            chain_head_sha256=head,
            records_sha256=records_hash,
            provenance=dict(provenance),
        )
        (path / "manifest.json").write_text(
            json.dumps(manifest.__dict__, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return manifest

    @staticmethod
    def verify(directory: str | Path) -> tuple[bool, str]:
        path = Path(directory)
        try:
            manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
            text = (path / "records.jsonl").read_text(encoding="utf-8")
        except Exception as exc:
            return False, f"bundle_read_error:{exc.__class__.__name__}"
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != manifest.get("records_sha256"):
            return False, "records_digest_mismatch"
        records: list[ChainedEvidenceRecord] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            doc = json.loads(line)
            records.append(ChainedEvidenceRecord(**doc))
        ok, reason = verify_records(records)
        if not ok:
            return False, reason
        head = records[-1].record_hash if records else "0" * 64
        if head != manifest.get("chain_head_sha256"):
            return False, "manifest_head_mismatch"
        if len(records) != int(manifest.get("record_count", -1)):
            return False, "record_count_mismatch"
        return True, "ok"
