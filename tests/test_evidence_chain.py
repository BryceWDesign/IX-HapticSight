import json
from dataclasses import replace

from ohip_evidence import EvidenceBundle, EvidenceChain, verify_records


def test_chain_verifies_and_detects_tamper(tmp_path):
    chain = EvidenceChain()
    chain.append("proposal", {"force_N": 4.0}, timestamp_s=1.0)
    chain.append("decision", {"force_N": 2.0}, timestamp_s=2.0)
    assert chain.verify() == (True, "ok")
    records = list(chain.records)
    records[0] = replace(records[0], payload={"force_N": 40.0})
    ok, reason = verify_records(records)
    assert not ok
    assert reason.startswith("record_hash_mismatch")


def test_bundle_roundtrip_and_digest_detection(tmp_path):
    chain = EvidenceChain()
    chain.append("a", {"x": 1}, timestamp_s=1.0)
    EvidenceBundle.write(tmp_path, chain.records, provenance={"mode": "test"})
    assert EvidenceBundle.verify(tmp_path) == (True, "ok")
    p = tmp_path / "records.jsonl"
    p.write_text(p.read_text() + "{}\n")
    assert EvidenceBundle.verify(tmp_path)[0] is False
