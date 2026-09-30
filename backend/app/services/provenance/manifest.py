"""JOCKY Platform — Provenance Manifest Generator"""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provenance import EvidenceManifest
from app.services.provenance.hasher import hash_evidence


async def create_manifest(
    evidence_record: dict[str, Any],
    script_hash: str,
    build_hash: str,
    db: AsyncSession
) -> EvidenceManifest:
    """
    Generate a cryptographic hash of the evidence and record its provenance.
    """
    evidence_hash = hash_evidence(evidence_record)
    
    manifest = EvidenceManifest(
        evidence_id=evidence_record.get("evidence_id"),
        case_id=evidence_record.get("case_id"),
        execution_id=evidence_record.get("execution_id"),
        host_id=evidence_record.get("host_id"),
        script_hash=script_hash,
        build_hash=build_hash,
        artifact_type=evidence_record.get("type"),
        collector_version=evidence_record.get("collector_version"),
        evidence_hash=evidence_hash,
    )
    
    db.add(manifest)
    return manifest
