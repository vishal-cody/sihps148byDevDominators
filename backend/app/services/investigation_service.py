"""JOCKY Platform — Investigation Service (background task executor)"""
import json
import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.investigation import Investigation, Execution
from app.models.findings import Finding, TimelineEvent
from app.models.evidence import ProcessRecord, NetworkConnection, PersistenceItem, EventLogRecord
from app.models.host import Host
from app.models.jocky import JockyBuild


async def run_investigation_task(
    investigation_id: str,
    host_ids: Optional[list] = None,
    build_id: Optional[str] = None,
    mode: str = "demo",
):
    """Background task: create jobs for agents OR run demo seeding."""
    async with AsyncSessionLocal() as db:
        q = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
        inv = q.scalar_one_or_none()
        if not inv:
            return

        assigned = host_ids or json.loads(inv.assigned_hosts or "[]")
        inv.started_at = datetime.utcnow()
        inv.status = "running"
        await db.flush()
        
        # Build ID handling
        actual_build_id = build_id
        if not actual_build_id and inv.jocky_script_id:
            # Get latest build for script
            bq = await db.execute(
                select(JockyBuild)
                .where(JockyBuild.script_id == inv.jocky_script_id)
                .order_by(JockyBuild.created_at.desc())
            )
            latest_build = bq.scalars().first()
            if latest_build:
                actual_build_id = latest_build.id

        if mode == "live":
            # LIVE MODE: Create QUEUED jobs for actual endpoint agents
            for host_id in assigned:
                exec_rec = Execution(
                    investigation_id=investigation_id,
                    host_id=host_id,
                    status="queued",
                    build_id=actual_build_id,
                    started_at=datetime.utcnow(),
                )
                db.add(exec_rec)
            await db.commit()
            
            _broadcast({"type": "investigation_started", "investigation_id": investigation_id, "mode": "live"})
            return

        # DEMO MODE: Fallback to current demo logic
        for host_id in assigned:
            exec_rec = Execution(
                investigation_id=investigation_id,
                host_id=host_id,
                status="collecting",
                build_id=actual_build_id,
                started_at=datetime.utcnow(),
            )
            db.add(exec_rec)
            await db.flush()

            # Simulate collection delay
            await asyncio.sleep(0.5)

            # Pull host info
            hq = await db.execute(select(Host).where(Host.id == host_id))
            host = hq.scalar_one_or_none()
            is_suspicious = host and not host.hostname.endswith("-003")  # demo_003 = clean

            # Generate demo evidence
            await _seed_demo_processes(db, investigation_id, exec_rec.id, host_id, is_suspicious)
            await _seed_demo_network(db, investigation_id, exec_rec.id, host_id, is_suspicious)
            await _seed_demo_persistence(db, investigation_id, exec_rec.id, host_id, is_suspicious)
            await _seed_demo_events(db, investigation_id, exec_rec.id, host_id, is_suspicious)

            exec_rec.status = "analyzing"
            await db.flush()

            # Run analyzer
            from app.analyzers.rule_engine import run_rules
            findings = await run_rules(investigation_id, host_id, db)
            for f in findings:
                db.add(f)

            # Build timeline
            from app.services.timeline_service import build_timeline
            events = await build_timeline(investigation_id, host_id, db)
            for e in events:
                db.add(e)

            exec_rec.status = "completed"
            exec_rec.completed_at = datetime.utcnow()
            await db.flush()

        inv.status = "completed"
        inv.completed_at = datetime.utcnow()
        await db.commit()

        _broadcast({
            "type": "investigation_complete",
            "investigation_id": investigation_id,
            "status": "completed",
            "mode": "demo"
        })


def _broadcast(payload: dict):
    try:
        from app.main import broadcast_event
        # Fire-and-forget sync wrapper or just create a task
        loop = asyncio.get_event_loop()
        loop.create_task(broadcast_event(payload))
    except Exception:
        pass


async def _seed_demo_processes(db, investigation_id, execution_id, host_id, is_suspicious):
    base_procs = [
        ("System", 4, 0, "C:\\Windows\\System32\\ntoskrnl.exe", "SYSTEM", 0.1, 12.0),
        ("svchost.exe", 812, 4, "C:\\Windows\\System32\\svchost.exe", "SYSTEM", 0.2, 45.0),
        ("explorer.exe", 2340, 812, "C:\\Windows\\explorer.exe", "user", 1.2, 85.0),
        ("chrome.exe", 4520, 2340, "C:\\Program Files\\Google\\Chrome\\chrome.exe", "user", 5.4, 320.0),
        ("python.exe", 6100, 2340, "C:\\Python311\\python.exe", "user", 0.8, 55.0),
    ]
    if is_suspicious:
        base_procs += [
            ("svch0st.exe", 9921, 812, "C:\\Users\\user\\AppData\\Local\\Temp\\svch0st.exe", "user", 15.3, 95.0),
            ("update.exe", 8834, 9921, "C:\\ProgramData\\update.exe", "user", 8.1, 42.0),
        ]
    for name, pid, ppid, path, user, cpu, mem in base_procs:
        p = ProcessRecord(
            execution_id=execution_id,
            host_id=host_id,
            investigation_id=investigation_id,
            pid=pid, ppid=ppid, name=name, path=path,
            username=user, cpu_percent=cpu, memory_mb=mem,
            status="running",
            created_time=datetime.utcnow() - timedelta(minutes=random.randint(1, 120)),
            is_suspicious=(is_suspicious and name in ("svch0st.exe", "update.exe")),
        )
        db.add(p)


async def _seed_demo_network(db, investigation_id, execution_id, host_id, is_suspicious):
    conns = [
        ("192.168.1.10", 52341, "8.8.8.8", 53, "UDP", "ESTABLISHED", None, "chrome.exe"),
        ("192.168.1.10", 49821, "142.250.80.46", 443, "TCP", "ESTABLISHED", 4520, "chrome.exe"),
        ("0.0.0.0", 3389, None, None, "TCP", "LISTEN", 812, "svchost.exe"),
    ]
    if is_suspicious:
        conns += [
            ("192.168.1.10", 44321, "185.220.101.47", 4444, "TCP", "ESTABLISHED", 9921, "svch0st.exe"),
            ("192.168.1.10", 55001, "93.184.216.34", 8080, "TCP", "ESTABLISHED", 8834, "update.exe"),
        ]
    for local_ip, local_port, remote_ip, remote_port, proto, state, pid, proc in conns:
        n = NetworkConnection(
            execution_id=execution_id,
            host_id=host_id,
            investigation_id=investigation_id,
            local_address=local_ip, local_port=local_port,
            remote_address=remote_ip, remote_port=remote_port,
            protocol=proto, state=state, pid=pid, process_name=proc,
            is_suspicious=(is_suspicious and remote_port in (4444, 8080) and remote_ip not in ("8.8.8.8",)),
        )
        db.add(n)


async def _seed_demo_persistence(db, investigation_id, execution_id, host_id, is_suspicious):
    items = [
        ("registry_run", "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
         "SecurityHealth", "C:\\Windows\\System32\\SecurityHealthSystray.exe", False),
        ("scheduled_task", "\\Microsoft\\Windows\\UpdateOrchestrator\\Schedule Scan",
         "Schedule Scan", "C:\\Windows\\System32\\UsoClient.exe StartScan", False),
    ]
    if is_suspicious:
        items += [
            ("registry_run",
             "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
             "Updater",
             "C:\\Users\\user\\AppData\\Local\\Temp\\svch0st.exe --persist",
             True),
            ("scheduled_task",
             "\\Microsoft\\Windows\\Maintenance\\updater_task",
             "updater_task",
             "C:\\ProgramData\\update.exe /silent",
             True),
        ]
    for cat, loc, name, cmd, susp in items:
        p = PersistenceItem(
            execution_id=execution_id,
            host_id=host_id,
            investigation_id=investigation_id,
            category=cat, location=loc, name=name,
            command=cmd, enabled=True,
            created_time=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
            is_suspicious=susp,
        )
        db.add(p)


async def _seed_demo_events(db, investigation_id, execution_id, host_id, is_suspicious):
    base_time = datetime.utcnow() - timedelta(hours=2)
    events = [
        (base_time, "Security", "authentication", 4624, "info", "Successful logon", "winlogon.exe", "user"),
        (base_time + timedelta(minutes=5), "System", "service_start", 7036, "info", "Windows Update service started", None, None),
        (base_time + timedelta(minutes=10), "Application", "application_event", 1000, "info", "Chrome updated", None, None),
    ]
    if is_suspicious:
        events += [
            (base_time + timedelta(minutes=15), "Security", "process_creation", 4688, "warning",
             "New process created: svch0st.exe from temp directory", "svch0st.exe", "user"),
            (base_time + timedelta(minutes=16), "Security", "network_event", 5156, "critical",
             "Outbound connection to 185.220.101.47:4444 (known C2 range)", "svch0st.exe", "user"),
            (base_time + timedelta(minutes=20), "Security", "registry_modification", 4657, "high",
             "Registry run key modified: HKCU\\Run\\Updater", "update.exe", "user"),
        ]
    for ts, src, etype, eid, sev, msg, proc, user in events:
        e = EventLogRecord(
            execution_id=execution_id,
            host_id=host_id,
            investigation_id=investigation_id,
            timestamp=ts, source=src, event_type=etype,
            event_id=eid, severity=sev, message=msg,
            process_id=None, user_name=user,
        )
        db.add(e)


async def process_agent_result(payload: dict, db):
    """Process uploaded agent job results (LIVE MODE)."""
    execution_id = payload.get("job_id")
    if not execution_id:
        return
        
    q = await db.execute(select(Execution).where(Execution.id == execution_id))
    exec_rec = q.scalar_one_or_none()
    if not exec_rec:
        return
        
    inv_id = exec_rec.investigation_id
    host_id = exec_rec.host_id
    
    results = payload.get("results", {})
    evidence_list = results.get("evidence", [])
    
    # Extract evidence into normalized tables
    from app.services.provenance.manifest import create_manifest
    script_hash = results.get("script_hash", "")
    build_hash = results.get("build_id", exec_rec.build_id or "")

    for item in evidence_list:
        await create_manifest(item, script_hash, build_hash, db)
        
        ev_type = item.get("type")
        data = item.get("payload", {})
        
        if ev_type == "PROCESS":
            p = ProcessRecord(
                execution_id=execution_id,
                host_id=host_id,
                investigation_id=inv_id,
                pid=data.get("pid", 0),
                ppid=data.get("ppid", 0),
                name=data.get("name", ""),
                path=data.get("path", ""),
                cmdline=data.get("cmdline", ""),
                username=data.get("username", ""),
                cpu_percent=data.get("cpu_percent", 0.0),
                memory_mb=data.get("memory_mb", 0.0),
                status=data.get("status", ""),
                created_time=datetime.fromisoformat(data.get("created_time")) if data.get("created_time") else None,
            )
            db.add(p)
            
        elif ev_type == "NETWORK_CONNECTION":
            n = NetworkConnection(
                execution_id=execution_id,
                host_id=host_id,
                investigation_id=inv_id,
                local_address=data.get("local_address", ""),
                local_port=data.get("local_port", 0),
                remote_address=data.get("remote_address", ""),
                remote_port=data.get("remote_port", 0),
                protocol=data.get("protocol", ""),
                state=data.get("state", ""),
                pid=data.get("pid", 0),
                process_name=data.get("process_name", ""),
            )
            db.add(n)
            
        elif ev_type == "SYSTEM_INFO":
            # Just create a dynamic record or if we have SystemInfo model
            pass
            
        elif ev_type == "FILE_METADATA":
            # If we had FileMetadata
            pass

    await db.flush()
    
    # Run analyzer
    from app.analyzers.rule_engine import run_rules
    findings = await run_rules(inv_id, host_id, db)
    for f in findings:
        db.add(f)

    # Build timeline
    from app.services.timeline_service import build_timeline
    events = await build_timeline(inv_id, host_id, db)
    for e in events:
        db.add(e)

    # Mark complete
    exec_rec.status = "completed"
    exec_rec.completed_at = datetime.utcnow()
    exec_rec.collection_stats = json.dumps(results.get("stats", {}))
    await db.flush()
    
    # Check if investigation is complete
    iq = await db.execute(select(Investigation).where(Investigation.id == inv_id))
    inv = iq.scalar_one_or_none()
    
    if inv:
        # Check all executions
        all_execs = await db.execute(select(Execution).where(Execution.investigation_id == inv_id))
        all_completed = all(e.status in ["completed", "failed"] for e in all_execs.scalars())
        if all_completed:
            inv.status = "completed"
            inv.completed_at = datetime.utcnow()
            
            _broadcast({
                "type": "investigation_complete",
                "investigation_id": inv_id,
                "status": "completed",
                "mode": "live"
            })
            
    await db.commit()
