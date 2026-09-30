"""JOCKY Platform — Hosts API"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.auth import get_current_user
from app.database import get_db
from app.models.host import Host, Agent
from app.models.user import User

router = APIRouter(prefix="/api/hosts", tags=["hosts"])


class HostSummary(BaseModel):
    id: str
    hostname: str
    display_name: Optional[str]
    ip_address: Optional[str]
    os_type: Optional[str]
    os_version: Optional[str]
    status: str
    last_seen: Optional[datetime]
    agent_version: Optional[str]
    is_demo: bool

    class Config:
        from_attributes = True


class HostDetail(HostSummary):
    architecture: Optional[str]
    cpu_model: Optional[str]
    ram_gb: Optional[float]
    domain: Optional[str]
    registered_at: datetime
    tags: Optional[str]


@router.get("", response_model=list[HostSummary])
async def list_hosts(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Host)
    if status:
        q = q.where(Host.status == status)
    q = q.order_by(Host.hostname)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/stats")
async def host_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    total = await db.scalar(select(func.count(Host.id)))
    online = await db.scalar(select(func.count(Host.id)).where(Host.status == "online"))
    offline = await db.scalar(select(func.count(Host.id)).where(Host.status == "offline"))
    investigating = await db.scalar(select(func.count(Host.id)).where(Host.status == "investigating"))
    return {
        "total": total,
        "online": online,
        "offline": offline,
        "investigating": investigating,
    }


@router.get("/{host_id}", response_model=HostDetail)
async def get_host(
    host_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Host).where(Host.id == host_id))
    host = result.scalar_one_or_none()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host
