"""JOCKY Platform — Provenance & Integrity Canonicalization"""
import json
from typing import Any

def canonicalize_evidence(evidence_record: dict[str, Any]) -> str:
    """
    Produce a deterministic, canonical JSON representation of an evidence record.
    Used for cryptographic hashing to ensure evidence hasn't been tampered with.
    """
    # Remove fields that might be modified post-collection (like UI display flags or local IDs)
    # Ensure we sort keys for deterministic output.
    clean_record = {
        "evidence_id": evidence_record.get("evidence_id"),
        "case_id": evidence_record.get("case_id"),
        "execution_id": evidence_record.get("execution_id"),
        "host_id": evidence_record.get("host_id"),
        "collector": evidence_record.get("collector"),
        "collector_version": evidence_record.get("collector_version"),
        "platform": evidence_record.get("platform"),
        "type": evidence_record.get("type"),
        "collected_at": evidence_record.get("collected_at"),
        "payload": evidence_record.get("payload", {}),
    }
    
    return json.dumps(clean_record, separators=(',', ':'), sort_keys=True, ensure_ascii=False)
