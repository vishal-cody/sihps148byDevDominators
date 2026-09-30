"""JOCKY Platform — Investigations API"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.investigation import Investigation, Execution
from app.models.findings import Finding, TimelineEvent

router = APIRouter(prefix="/api/investigations", tags=["investigations"])


class InvestigationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    priority: str = "medium"
    assigned_hosts: list[str] = []
    jocky_script_id: Optional[str] = None


class InvestigationSummary(BaseModel):
    id: str
    case_id: str
    name: str
    description: Optional[str]
    status: str
    priority: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    host_count: int = 0
    finding_count: int = 0
    high_findings: int = 0

    class Config:
        from_attributes = True


class RunRequest(BaseModel):
    host_ids: Optional[list[str]] = None
    build_id: Optional[str] = None
    mode: str = "live"


def _case_id() -> str:
    from datetime import date
    import random
    return f"INV-{date.today().year}-{random.randint(100,999)}"


@router.post("", response_model=dict)
async def create_investigation(
    payload: InvestigationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inv = Investigation(
        case_id=_case_id(),
        name=payload.name,
        description=payload.description,
        priority=payload.priority,
        assigned_hosts=json.dumps(payload.assigned_hosts),
        created_by=current_user.id,
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    return {"id": inv.id, "case_id": inv.case_id, "name": inv.name, "status": inv.status}


@router.get("", response_model=list[dict])
async def list_investigations(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Investigation).order_by(Investigation.created_at.desc())
    if status:
        q = q.where(Investigation.status == status)
    result = await db.execute(q)
    investigations = result.scalars().all()

    out = []
    for inv in investigations:
        hosts = json.loads(inv.assigned_hosts or "[]")
        findings_q = await db.execute(
            select(func.count(Finding.id)).where(Finding.investigation_id == inv.id)
        )
        finding_count = findings_q.scalar() or 0
        high_q = await db.execute(
            select(func.count(Finding.id)).where(
                Finding.investigation_id == inv.id,
                Finding.severity.in_(["high", "critical"])
            )
        )
        high_count = high_q.scalar() or 0
        out.append({
            "id": inv.id,
            "case_id": inv.case_id,
            "name": inv.name,
            "description": inv.description,
            "status": inv.status,
            "priority": inv.priority,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "started_at": inv.started_at.isoformat() if inv.started_at else None,
            "completed_at": inv.completed_at.isoformat() if inv.completed_at else None,
            "host_count": len(hosts),
            "finding_count": finding_count,
            "high_findings": high_count,
            "is_demo": inv.is_demo == "1" or inv.is_demo is True,
        })
    return out


@router.get("/stats")
async def investigation_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    total = await db.scalar(select(func.count(Investigation.id)))
    active = await db.scalar(
        select(func.count(Investigation.id)).where(Investigation.status.in_(["running", "created"]))
    )
    high = await db.scalar(
        select(func.count(Finding.id)).where(Finding.severity.in_(["high", "critical"]))
    )
    medium = await db.scalar(
        select(func.count(Finding.id)).where(Finding.severity == "medium")
    )
    low = await db.scalar(
        select(func.count(Finding.id)).where(Finding.severity == "low")
    )
    return {
        "total_investigations": total,
        "active_investigations": active,
        "high_findings": high,
        "medium_findings": medium,
        "low_findings": low,
    }


@router.get("/{inv_id}")
async def get_investigation(
    inv_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Investigation).where(Investigation.id == inv_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    execs_q = await db.execute(select(Execution).where(Execution.investigation_id == inv_id))
    executions = execs_q.scalars().all()

    findings_q = await db.execute(select(Finding).where(Finding.investigation_id == inv_id))
    findings = findings_q.scalars().all()

    return {
        "id": inv.id, "case_id": inv.case_id, "name": inv.name,
        "description": inv.description, "status": inv.status,
        "priority": inv.priority,
        "assigned_hosts": json.loads(inv.assigned_hosts or "[]"),
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "started_at": inv.started_at.isoformat() if inv.started_at else None,
        "completed_at": inv.completed_at.isoformat() if inv.completed_at else None,
        "is_demo": inv.is_demo == "1" or inv.is_demo is True,
        "jocky_script_id": inv.jocky_script_id,
        "executions": [
            {"id": e.id, "host_id": e.host_id, "status": e.status,
             "started_at": e.started_at.isoformat() if e.started_at else None,
             "completed_at": e.completed_at.isoformat() if e.completed_at else None}
            for e in executions
        ],
        "findings_summary": {
            "total": len(findings),
            "critical": sum(1 for f in findings if f.severity == "critical"),
            "high": sum(1 for f in findings if f.severity == "high"),
            "medium": sum(1 for f in findings if f.severity == "medium"),
            "low": sum(1 for f in findings if f.severity == "low"),
        }
    }


@router.post("/{inv_id}/run")
async def run_investigation(
    inv_id: str,
    payload: RunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Investigation).where(Investigation.id == inv_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    from app.services.investigation_service import run_investigation_task
    background_tasks.add_task(run_investigation_task, inv_id, payload.host_ids, payload.build_id, payload.mode)

    inv.status = "running"
    inv.started_at = datetime.utcnow()
    await db.commit()

    return {"message": "Investigation dispatched", "investigation_id": inv_id, "status": "running"}
