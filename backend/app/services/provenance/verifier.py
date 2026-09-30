"""JOCKY Platform — Provenance Verifier"""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.provenance import EvidenceManifest
from app.services.provenance.hasher import hash_evidence


async def verify_evidence(evidence_record: dict[str, Any], db: AsyncSession) -> dict[str, Any]:
    """
    Verify that an evidence record matches its stored cryptographic hash.
    """
    evidence_id = evidence_record.get("evidence_id")
    if not evidence_id:
        return {"status": "INVALID", "reason": "No evidence_id provided"}
        
    q = await db.execute(select(EvidenceManifest).where(EvidenceManifest.evidence_id == evidence_id))
    manifest = q.scalar_one_or_none()
    
    if not manifest:
        return {"status": "NOT_FOUND", "reason": f"No manifest found for evidence_id {evidence_id}"}
        
    computed_hash = hash_evidence(evidence_record)
    
    if computed_hash == manifest.evidence_hash:
        return {
            "status": "VALID",
            "expected_hash": manifest.evidence_hash,
            "computed_hash": computed_hash,
            "manifest_id": manifest.id,
            "script_hash": manifest.script_hash,
            "build_hash": manifest.build_hash,
        }
    else:
        return {
            "status": "MODIFIED",
            "expected_hash": manifest.evidence_hash,
            "computed_hash": computed_hash,
            "reason": "Hash mismatch — evidence may have been tampered with",
        }
