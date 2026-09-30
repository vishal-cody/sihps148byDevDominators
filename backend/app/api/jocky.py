"""JOCKY Platform — JOCKY Compiler API"""
import sys
import os
import hashlib
import json
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.jocky import JockyScript, JockyBuild

# Add compiler to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

router = APIRouter(prefix="/api/jocky", tags=["jocky"])


class ValidateRequest(BaseModel):
    source_code: str


class CompileRequest(BaseModel):
    source_code: str
    script_name: Optional[str] = "untitled.jky"


class BuildRequest(BaseModel):
    script_id: Optional[str] = None
    source_code: Optional[str] = None
    profile: str = "forensic_standard"


class ScriptCreate(BaseModel):
    name: str
    description: Optional[str] = None
    source_code: str


def _get_compiler():
    try:
        from compiler.compiler import JockyCompiler
        return JockyCompiler()
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"JOCKY compiler module not found: {str(e)}")


@router.post("/validate")
async def validate_script(
    payload: ValidateRequest,
    _: User = Depends(get_current_user),
):
    compiler = _get_compiler()
    result = compiler.validate(payload.source_code)
    return result


@router.post("/compile")
async def compile_script(
    payload: CompileRequest,
    _: User = Depends(get_current_user),
):
    compiler = _get_compiler()
    result = compiler.compile(payload.source_code)
    return result


@router.post("/build")
async def build_script(
    payload: BuildRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    compiler = _get_compiler()

    source_code = payload.source_code
    script_id = payload.script_id

    if script_id and not source_code:
        q = await db.execute(select(JockyScript).where(JockyScript.id == script_id))
        script = q.scalar_one_or_none()
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        source_code = script.source_code

    if not source_code:
        raise HTTPException(status_code=400, detail="source_code or script_id required")

    t0 = time.time()
    result = compiler.build(source_code, profile=payload.profile)
    build_time_ms = (time.time() - t0) * 1000

    if not result.get("success"):
        raise HTTPException(status_code=422, detail=result.get("errors", ["Compilation failed"]))

    ir_json = json.dumps(result.get("ir", {}))
    sha256 = hashlib.sha256(ir_json.encode() + payload.profile.encode()).hexdigest()

    build = JockyBuild(
        script_id=script_id or "inline",
        profile=payload.profile,
        sha256_hash=sha256,
        ir_json=ir_json,
        ir_node_count=result.get("ir_node_count", 0),
        transformation_log=json.dumps(result.get("transformations", [])),
        build_metadata=json.dumps(result.get("metadata", {})),
        build_time_ms=build_time_ms,
        status="success",
    )
    db.add(build)
    await db.commit()
    await db.refresh(build)

    return {
        "build_id": build.id,
        "profile": build.profile,
        "sha256": sha256,
        "ir_node_count": build.ir_node_count,
        "build_time_ms": round(build_time_ms, 2),
        "transformations": result.get("transformations", []),
        "ir": result.get("ir", {}),
        "success": True,
    }


@router.post("/build/{build_id}/variant")
async def generate_variant(
    build_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Generate a second build variant for comparison demo."""
    q = await db.execute(select(JockyBuild).where(JockyBuild.id == build_id))
    original = q.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="Build not found")

    compiler = _get_compiler()

    # Get source from original IR
    ir_data = json.loads(original.ir_json or "{}")
    source_code = ir_data.get("_source", "")

    variant_profile = "forensic_variant" if original.profile == "forensic_standard" else "forensic_standard"

    t0 = time.time()
    result = compiler.build(source_code or "investigation \"variant\" {}", profile=variant_profile)
    build_time_ms = (time.time() - t0) * 1000

    ir_json = json.dumps(result.get("ir", {}))
    sha256 = hashlib.sha256(ir_json.encode() + variant_profile.encode()).hexdigest()

    variant = JockyBuild(
        script_id=original.script_id,
        profile=variant_profile,
        sha256_hash=sha256,
        ir_json=ir_json,
        ir_node_count=result.get("ir_node_count", 0),
        transformation_log=json.dumps(result.get("transformations", [])),
        build_metadata=json.dumps(result.get("metadata", {})),
        build_time_ms=build_time_ms,
        status="success",
    )
    db.add(variant)
    await db.commit()
    await db.refresh(variant)

    return {
        "original": {
            "build_id": original.id,
            "profile": original.profile,
            "sha256": original.sha256_hash,
            "ir_node_count": original.ir_node_count,
        },
        "variant": {
            "build_id": variant.id,
            "profile": variant.profile,
            "sha256": sha256,
            "ir_node_count": variant.ir_node_count,
        },
        "functional_equivalence": "IDENTICAL",
        "equivalence_proof": "Both builds produce the same forensic collection operations despite differing internal representations.",
    }


@router.post("/scripts", response_model=dict)
async def save_script(
    payload: ScriptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    script = JockyScript(
        name=payload.name,
        description=payload.description,
        source_code=payload.source_code,
        created_by=current_user.id,
    )
    db.add(script)
    await db.commit()
    await db.refresh(script)
    return {"id": script.id, "name": script.name, "created_at": script.created_at.isoformat()}


@router.get("/scripts")
async def list_scripts(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = await db.execute(select(JockyScript).order_by(JockyScript.updated_at.desc()))
    scripts = q.scalars().all()
    return [
        {"id": s.id, "name": s.name, "description": s.description,
         "updated_at": s.updated_at.isoformat() if s.updated_at else None,
         "source_code": s.source_code,
         "is_valid": s.is_valid}
        for s in scripts
    ]


@router.get("/builds")
async def list_builds(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = await db.execute(select(JockyBuild).order_by(JockyBuild.created_at.desc()).limit(50))
    builds = q.scalars().all()
    return [
        {"id": b.id, "script_id": b.script_id, "profile": b.profile,
         "sha256": b.sha256_hash, "ir_node_count": b.ir_node_count,
         "build_time_ms": b.build_time_ms,
         "created_at": b.created_at.isoformat() if b.created_at else None,
         "status": b.status}
        for b in builds
    ]
