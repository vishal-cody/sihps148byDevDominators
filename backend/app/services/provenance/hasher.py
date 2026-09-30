"""JOCKY Platform — Provenance Hasher"""
import hashlib
from typing import Any

from app.services.provenance.canonicalizer import canonicalize_evidence


def hash_evidence(evidence_record: dict[str, Any]) -> str:
    """
    Produce a SHA-256 hash of a normalized evidence record.
    """
    canonical_string = canonicalize_evidence(evidence_record)
    return hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()
