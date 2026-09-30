"""JOCKY Platform — Agents API (register, heartbeat, job poll, result upload)"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.host import Host, Agent
from app.models.investigation import Execution, Investigation
from app.models.jocky import JockyBuild
from app.models.user import User

settings = get_settings()
router = APIRouter(prefix="/api/agents", tags=["agents"])


class RegisterRequest(BaseModel):
    agent_id: str
    host_id: Optional[str] = None
    hostname: str
    platform: str
    os_version: Optional[str] = None
    architecture: Optional[str] = None
    version: str
    capabilities: list[str] = []
    ip_address: Optional[str] = None


class HeartbeatRequest(BaseModel):
    agent_id: str
    status: str = "online"


class JobResultRequest(BaseModel):
    agent_id: str
    job_id: str
    results: dict


@router.post("/register")
async def register_agent(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    # Find or create host
    q = await db.execute(select(Host).where(Host.hostname == payload.hostname))
    host = q.scalar_one_or_none()

    if not host:
        host = Host(
            hostname=payload.hostname,
            ip_address=payload.ip_address,
            os_type=payload.platform,
            os_version=payload.os_version,
            agent_version=payload.version,
            status="online",
            last_seen=datetime.utcnow(),
        )
        db.add(host)
        await db.flush()

    host.status = "online"
    host.last_seen = datetime.utcnow()
    host.agent_version = payload.version

    # Find or create agent record
    q2 = await db.execute(select(Agent).where(Agent.agent_key == payload.agent_id))
    agent = q2.scalar_one_or_none()
    if not agent:
        agent = Agent(
            host_id=host.id,
            agent_key=payload.agent_id,
            version=payload.version,
            platform=payload.platform,
            capabilities=json.dumps(payload.capabilities),
            status="idle",
        )
        db.add(agent)

    agent.last_heartbeat = datetime.utcnow()
    await db.commit()

    return {"host_id": host.id, "agent_id": agent.id, "token": "demo_agent_token", "status": "registered"}


@router.post("/heartbeat")
async def heartbeat(
    payload: HeartbeatRequest,
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(select(Agent).where(Agent.agent_key == payload.agent_id))
    agent = q.scalar_one_or_none()
    if agent:
        agent.last_heartbeat = datetime.utcnow()
        agent.status = payload.status

        q2 = await db.execute(select(Host).where(Host.id == agent.host_id))
        host = q2.scalar_one_or_none()
        if host:
            host.last_seen = datetime.utcnow()
            host.status = "online"

    await db.commit()
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@router.get("/jobs/{agent_id}")
async def poll_jobs(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Agent polls for pending jobs."""
    q = await db.execute(select(Agent).where(Agent.agent_key == agent_id))
    agent = q.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    host_id = agent.host_id
    
    # Find queued executions for this host
    eq = await db.execute(
        select(Execution, Investigation)
        .join(Investigation, Execution.investigation_id == Investigation.id)
        .where(Execution.host_id == host_id, Execution.status == "queued")
    )
    results = eq.all()
    
    jobs = []
    for exec_rec, inv in results:
        # Get the IR
        build_id = exec_rec.build_id
        if build_id:
            bq = await db.execute(select(JockyBuild).where(JockyBuild.id == build_id))
            build = bq.scalar_one_or_none()
            if build and build.ir_json:
                jobs.append({
                    "job_id": exec_rec.id,
                    "execution_id": exec_rec.id,
                    "case_id": inv.case_id,
                    "investigation_id": inv.id,
                    "host_id": host_id,
                    "build_id": build.id,
                    "script_hash": build.sha256_hash,
                    "ir": json.loads(build.ir_json),
                })
                exec_rec.status = "dispatched"
                
    await db.commit()
    return {"jobs": jobs, "timestamp": datetime.utcnow().isoformat()}


@router.post("/results")
async def upload_results(
    payload: JobResultRequest,
    db: AsyncSession = Depends(get_db),
):
    from app.services.investigation_service import process_agent_result
    await process_agent_result(payload.dict(), db)
    return {"status": "accepted"}
