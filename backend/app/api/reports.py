"""JOCKY Platform — Reports API"""
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.findings import Report
from app.models.investigation import Investigation

settings = get_settings()
router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportRequest(BaseModel):
    format: str = "json"  # pdf, json, csv


@router.post("/{investigation_id}")
async def generate_report(
    investigation_id: str,
    payload: ReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    inv = q.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    report = Report(
        investigation_id=investigation_id,
        format=payload.format,
        filename=f"JOCKY_Report_{inv.case_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{payload.format}",
        generated_by=current_user.id,
        status="generating",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    from app.services.report_service import generate_report_task
    background_tasks.add_task(generate_report_task, report.id, investigation_id, payload.format)

    return {"report_id": report.id, "status": "generating", "format": payload.format}


@router.get("/{investigation_id}")
async def list_reports(
    investigation_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = await db.execute(
        select(Report).where(Report.investigation_id == investigation_id)
        .order_by(Report.generated_at.desc())
    )
    reports = q.scalars().all()
    return [
        {"id": r.id, "format": r.format, "filename": r.filename,
         "status": r.status, "file_size_bytes": r.file_size_bytes,
         "generated_at": r.generated_at.isoformat() if r.generated_at else None}
        for r in reports
    ]


@router.get("/download/{report_id}")
async def download_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = await db.execute(select(Report).where(Report.id == report_id))
    report = q.scalar_one_or_none()
    if not report or not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(
        report.file_path,
        media_type="application/octet-stream",
        filename=report.filename,
    )
