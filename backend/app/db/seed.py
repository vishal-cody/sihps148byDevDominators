"""JOCKY Platform — Demo Data Seeder (INV-2025-001)
Creates 5 hosts, 1 investigation, and full evidence dataset for SIH demo.
"""
import json
import random
import asyncio
from datetime import datetime, timedelta

from app.database import AsyncSessionLocal, create_all_tables
from app.auth import hash_password
from app.models.user import User, UserRole
from app.models.host import Host, Agent
from app.models.investigation import Investigation, Execution
from app.models.evidence import ProcessRecord, NetworkConnection, PersistenceItem, EventLogRecord
from app.models.jocky import JockyScript, JockyBuild
from app.models.findings import Finding, TimelineEvent, Report


DEMO_HOSTS = [
    {"hostname": "HOST-001", "os": "windows", "os_ver": "Windows 11 Pro 23H2",
     "ip": "192.168.10.101", "suspicious": True, "scenario": "malware"},
    {"hostname": "HOST-002", "os": "windows", "os_ver": "Windows 10 Pro 22H2",
     "ip": "192.168.10.102", "suspicious": True, "scenario": "c2"},
    {"hostname": "HOST-003", "os": "linux", "os_ver": "Ubuntu 22.04 LTS",
     "ip": "192.168.10.103", "suspicious": False, "scenario": "clean"},
    {"hostname": "HOST-004", "os": "windows", "os_ver": "Windows Server 2022",
     "ip": "192.168.10.104", "suspicious": True, "scenario": "persistence"},
    {"hostname": "HOST-005", "os": "linux", "os_ver": "Ubuntu 20.04 LTS",
     "ip": "192.168.10.105", "suspicious": False, "scenario": "clean"},
]

DEMO_SCRIPT = '''\
investigation "Enterprise Security Sweep — INV-2025-001" {
    collect system_info
    collect processes
    collect network_connections
    collect persistence
    collect event_logs
    collect filesystem

    analyze processes
    analyze network_connections
    analyze persistence

    filter processes where cpu > 10
    filter network_connections where port in [4444, 1337, 8080]

    generate timeline
    generate report
}
'''

BASE_TIME = datetime.utcnow() - timedelta(hours=3)


async def seed_all():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func

        # Check already seeded
        existing = await db.scalar(select(func.count(User.id)))
        if existing and existing > 0:
            print("[SEED] Already seeded, skipping.")
            return

        print("[SEED] Starting demo data seed...")

        # ── Users ─────────────────────────────────────────────────────
        users = [
            User(username="admin", email="admin@jocky.local",
                 hashed_password=hash_password("admin123"),
                 full_name="JOCKY Administrator", role=UserRole.admin, is_active=True),
            User(username="demo_admin", email="demo@jocky.local",
                 hashed_password=hash_password("demo123"),
                 full_name="Demo Administrator", role=UserRole.admin, is_active=True),
            User(username="investigator", email="investigator@jocky.local",
                 hashed_password=hash_password("inv123"),
                 full_name="Lead Investigator", role=UserRole.investigator, is_active=True),
            User(username="viewer", email="viewer@jocky.local",
                 hashed_password=hash_password("view123"),
                 full_name="SOC Analyst", role=UserRole.viewer, is_active=True),
        ]
        for u in users:
            db.add(u)
        await db.flush()
        admin_id = users[0].id

        # ── Hosts ──────────────────────────────────────────────────────
        host_objs = []
        for h in DEMO_HOSTS:
            host = Host(
                hostname=h["hostname"],
                display_name=h["hostname"],
                ip_address=h["ip"],
                os_type=h["os"],
                os_version=h["os_ver"],
                architecture="x86_64",
                cpu_model="Intel Core i7-12700K",
                ram_gb=16.0,
                domain="CORP.LOCAL",
                agent_version="1.0.0",
                status="online" if h["hostname"] != "HOST-003" else "offline",
                last_seen=datetime.utcnow() - (timedelta(minutes=4) if h["hostname"] == "HOST-003" else timedelta(seconds=random.randint(2, 30))),
                is_demo=True,
                tags=json.dumps(["demo", h["scenario"]]),
            )
            db.add(host)
            host_objs.append(host)
        await db.flush()

        # ── JOCKY Script ───────────────────────────────────────────────
        script = JockyScript(
            name="Enterprise Security Sweep",
            description="Standard enterprise-wide security sweep investigating processes, network, and persistence",
            source_code=DEMO_SCRIPT,
            created_by=admin_id,
            is_valid=True,
        )
        db.add(script)
        await db.flush()

        # ── JOCKY Build (two variants) ─────────────────────────────────
        import hashlib
        ir_standard = json.dumps({
            "type": "investigation", "name": "Enterprise Security Sweep",
            "_source": DEMO_SCRIPT,
            "operations": [
                {"op": "COLLECT", "target": "SYSTEM_INFO"},
                {"op": "COLLECT", "target": "PROCESSES"},
                {"op": "COLLECT", "target": "NETWORK_CONNECTIONS"},
                {"op": "COLLECT", "target": "PERSISTENCE"},
                {"op": "COLLECT", "target": "EVENT_LOGS"},
                {"op": "ANALYZE", "target": "PROCESSES"},
                {"op": "ANALYZE", "target": "NETWORK_CONNECTIONS"},
                {"op": "FILTER", "target": "PROCESSES", "condition": "cpu > 10"},
                {"op": "GENERATE_TIMELINE"},
                {"op": "GENERATE_REPORT"},
            ]
        })
        ir_variant = json.dumps({
            "type": "investigation", "name": "Enterprise Security Sweep",
            "_source": DEMO_SCRIPT,
            "build_id": "variant_b",
            "operations": [
                {"op": "FETCH_SYSINFO", "target": "SYSTEM_INFO"},
                {"op": "ENUM_PROCESSES", "target": "PROCESSES"},
                {"op": "ENUM_NETCONN", "target": "NETWORK_CONNECTIONS"},
                {"op": "ENUM_PERSIST", "target": "PERSISTENCE"},
                {"op": "FETCH_EVTLOG", "target": "EVENT_LOGS"},
                {"op": "RUN_ANALYSIS", "target": "PROCESSES"},
                {"op": "RUN_ANALYSIS", "target": "NETWORK_CONNECTIONS"},
                {"op": "APPLY_FILTER", "target": "PROCESSES", "condition": "cpu > 10"},
                {"op": "BUILD_TIMELINE"},
                {"op": "EMIT_REPORT"},
            ]
        })

        build_a = JockyBuild(
            script_id=script.id, build_number=1,
            profile="forensic_standard",
            sha256_hash=hashlib.sha256(ir_standard.encode()).hexdigest(),
            ir_json=ir_standard, ir_node_count=10,
            transformation_log=json.dumps(["identifier_rename", "constant_representation"]),
            build_metadata=json.dumps({"build_id": "A", "timestamp": datetime.utcnow().isoformat()}),
            build_time_ms=142.3, status="success",
        )
        build_b = JockyBuild(
            script_id=script.id, build_number=2,
            profile="forensic_variant",
            sha256_hash=hashlib.sha256(ir_variant.encode()).hexdigest(),
            ir_json=ir_variant, ir_node_count=12,
            transformation_log=json.dumps(["identifier_rename", "operation_reorder", "metadata_variation"]),
            build_metadata=json.dumps({"build_id": "B", "timestamp": datetime.utcnow().isoformat(), "variant": True}),
            build_time_ms=189.7, status="success",
        )
        db.add(build_a)
        db.add(build_b)
        await db.flush()

        script.last_build_id = build_a.id
        script.last_compiled = datetime.utcnow()

        # ── Investigation ──────────────────────────────────────────────
        host_id_list = [h.id for h in host_objs]
        inv = Investigation(
            case_id="INV-2025-001",
            name="Enterprise Security Sweep — Q3 2025",
            description="Full enterprise sweep following detection of anomalous outbound traffic on HOST-001 and HOST-002. Investigation covers all 5 corporate endpoints.",
            status="completed",
            priority="high",
            assigned_hosts=json.dumps(host_id_list),
            created_by=admin_id,
            created_at=BASE_TIME,
            started_at=BASE_TIME + timedelta(minutes=2),
            completed_at=BASE_TIME + timedelta(minutes=45),
            jocky_script_id=script.id,
            is_demo="1",
        )
        db.add(inv)
        await db.flush()

        # ── Executions + Evidence ──────────────────────────────────────
        for i, host in enumerate(host_objs):
            h_cfg = DEMO_HOSTS[i]
            exec_rec = Execution(
                investigation_id=inv.id, host_id=host.id,
                status="completed", build_id=build_a.id,
                started_at=BASE_TIME + timedelta(minutes=3+i*5),
                completed_at=BASE_TIME + timedelta(minutes=8+i*5),
            )
            db.add(exec_rec)
            await db.flush()

            is_sus = h_cfg["suspicious"]
            scenario = h_cfg["scenario"]

            # Processes
            await _add_processes(db, inv.id, exec_rec.id, host.id, is_sus, scenario, BASE_TIME)
            # Network
            await _add_network(db, inv.id, exec_rec.id, host.id, is_sus, scenario)
            # Persistence
            await _add_persistence(db, inv.id, exec_rec.id, host.id, is_sus, scenario, BASE_TIME)
            # Event logs
            await _add_events(db, inv.id, exec_rec.id, host.id, is_sus, scenario, BASE_TIME)

        await db.flush()

        # ── Findings ──────────────────────────────────────────────────
        findings_data = [
            # HOST-001 malware
            {"host": host_objs[0], "title": "Typosquatted System Process Detected", "sev": "critical", "conf": 0.94,
             "cat": "process", "rule": "PROC-002", "mitre": "T1036.004",
             "desc": "Process 'svch0st.exe' (PID:9921) running from AppData\\Local\\Temp closely resembles legitimate 'svchost.exe'. Binary hash does not match known-good Windows binary.",
             "rec": "Immediately terminate PID 9921, quarantine binary, collect memory dump, and block hash at EDR."},
            {"host": host_objs[0], "title": "C2 Network Connection — Port 4444", "sev": "critical", "conf": 0.91,
             "cat": "network", "rule": "NET-001", "mitre": "T1071.001",
             "desc": "Outbound TCP connection from svch0st.exe (PID:9921) to 185.220.101.47:4444. Port 4444 is associated with Metasploit meterpreter C2 framework. IP falls within Tor exit node range.",
             "rec": "Block 185.220.0.0/16 subnet at perimeter firewall. Initiate incident response for HOST-001."},
            {"host": host_objs[0], "title": "Malicious Registry Run Key", "sev": "high", "conf": 0.86,
             "cat": "persistence", "rule": "PERSIST-001", "mitre": "T1547.001",
             "desc": "Registry key HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run\\Updater created pointing to C:\\Users\\user\\AppData\\Local\\Temp\\svch0st.exe. Created within investigation window.",
             "rec": "Remove registry run key immediately. Investigate when this was created and by what parent process."},
            # HOST-002 c2
            {"host": host_objs[1], "title": "Secondary C2 Beaconing Detected", "sev": "critical", "conf": 0.89,
             "cat": "network", "rule": "NET-002", "mitre": "T1071.001",
             "desc": "Outbound connection from update.exe to 93.184.216.34:8080. Traffic pattern shows 60-second beaconing interval consistent with staged C2 communication.",
             "rec": "Block destination IP, isolate HOST-002 from network, preserve RAM for forensic analysis."},
            {"host": host_objs[1], "title": "Malicious Scheduled Task", "sev": "high", "conf": 0.83,
             "cat": "persistence", "rule": "PERSIST-002", "mitre": "T1053.005",
             "desc": "Scheduled task '\\Microsoft\\Windows\\Maintenance\\updater_task' executes C:\\ProgramData\\update.exe /silent on system startup.",
             "rec": "Delete scheduled task, quarantine update.exe binary, scan ProgramData for additional malware."},
            {"host": host_objs[1], "title": "Suspicious Process in ProgramData", "sev": "high", "conf": 0.87,
             "cat": "process", "rule": "PROC-001", "mitre": "T1204.002",
             "desc": "Process 'update.exe' running from C:\\ProgramData\\update.exe. Legitimate update utilities do not reside in ProgramData root.",
             "rec": "Terminate process, hash file, check against threat intel databases."},
            # HOST-004 persistence
            {"host": host_objs[3], "title": "Unusual Service Installation", "sev": "medium", "conf": 0.75,
             "cat": "persistence", "rule": "PERSIST-002", "mitre": "T1543.003",
             "desc": "New Windows service 'DataSync' installed with binary path pointing to non-standard location C:\\ProgramData\\DataSync\\agent.exe.",
             "rec": "Investigate service origin, verify binary authenticity via hash comparison."},
            {"host": host_objs[3], "title": "High CPU Suspicious Process", "sev": "medium", "conf": 0.72,
             "cat": "process", "rule": "PROC-003", "mitre": "T1496",
             "desc": "Process svch0st.exe consuming 15.3% CPU consistently — pattern consistent with cryptomining or periodic beaconing.",
             "rec": "Monitor process behaviour over 24h window, capture network traffic."},
            # Medium and low findings
            {"host": host_objs[0], "title": "Process Tree Anomaly", "sev": "medium", "conf": 0.78,
             "cat": "process", "rule": "PROC-001", "mitre": "T1055",
             "desc": "svch0st.exe spawned from svchost.exe (PID:812) — unexpected parent-child relationship.",
             "rec": "Investigate parent process chain. Verify svchost.exe integrity."},
            {"host": host_objs[1], "title": "Outbound Connection on Non-Standard Port", "sev": "medium", "conf": 0.68,
             "cat": "network", "rule": "NET-001", "mitre": "T1571",
             "desc": "Connection to external IP on port 8080 — not standard for enterprise HTTP proxy configuration.",
             "rec": "Review proxy bypass policy, ensure all HTTP traffic routes through corporate proxy."},
            {"host": host_objs[3], "title": "Authentication from New Host", "sev": "low", "conf": 0.61,
             "cat": "authentication", "rule": "AUTH-001", "mitre": "T1078",
             "desc": "User 'admin' logged in from HOST-004 — first authentication from this host in 30 days.",
             "rec": "Verify with user if this login was expected."},
        ]

        for fd in findings_data:
            f = Finding(
                investigation_id=inv.id,
                host_id=fd["host"].id,
                title=fd["title"], description=fd["desc"],
                severity=fd["sev"], confidence=fd["conf"],
                category=fd["cat"], rule_id=fd["rule"],
                mitre_technique=fd["mitre"],
                recommendation=fd["rec"],
                status="open",
                created_at=BASE_TIME + timedelta(minutes=random.randint(30, 44)),
            )
            db.add(f)

        # ── Timeline events (100+) ─────────────────────────────────────
        timeline_events = _build_full_timeline(inv.id, host_objs, BASE_TIME)
        for te in timeline_events:
            db.add(te)

        await db.commit()
        print(f"[SEED] ✓ Demo data created: {len(host_objs)} hosts, 1 investigation, {len(findings_data)} findings, {len(timeline_events)} timeline events")


def _build_full_timeline(inv_id, hosts, base_time):
    events = []
    t = base_time

    # System startup events for all hosts
    for host in hosts:
        for i, (etype, sev, title, desc) in enumerate([
            ("system_event", "info", "System boot", "Windows boot sequence initiated"),
            ("system_event", "info", "Services started", "Core Windows services started"),
            ("authentication", "info", "User logon", "Interactive logon: user authenticated"),
            ("process_start", "info", "Explorer started", "Windows shell (explorer.exe) started"),
            ("process_start", "info", "AV started", "Antivirus protection active"),
        ]):
            events.append(TimelineEvent(
                investigation_id=inv_id, host_id=host.id,
                timestamp=t + timedelta(minutes=i * 2),
                event_type=etype, severity=sev, title=title, description=desc,
                actor="SYSTEM", is_suspicious=False,
            ))

    # Suspicious events for HOST-001
    h001 = hosts[0]
    t1 = base_time + timedelta(minutes=15)
    sus_events_001 = [
        ("process_start", "warning", "Unusual process created", "svch0st.exe spawned from svchost.exe in AppData\\Temp", "svch0st.exe", True),
        ("network_connect", "critical", "C2 connection established", "svch0st.exe → 185.220.101.47:4444 (Tor exit, Metasploit C2)", "svch0st.exe", True),
        ("persistence_created", "high", "Registry run key added", "HKCU\\Run\\Updater → AppData\\Temp\\svch0st.exe", "svch0st.exe", True),
        ("file_created", "high", "Dropper written to disk", "C:\\Users\\user\\AppData\\Local\\Temp\\svch0st.exe created", "update.exe", True),
        ("network_connect", "high", "Data exfiltration beacon", "Periodic 60s beaconing to C2 server", "svch0st.exe", True),
        ("process_start", "high", "Secondary payload launched", "update.exe started from ProgramData", "svch0st.exe", True),
        ("persistence_created", "high", "Scheduled task created", "\\Microsoft\\Windows\\Maintenance\\updater_task", "update.exe", True),
        ("system_event", "warning", "Registry modification", "Multiple run keys modified in HKCU hive", "update.exe", True),
    ]
    for i, (etype, sev, title, desc, actor, sus) in enumerate(sus_events_001):
        events.append(TimelineEvent(
            investigation_id=inv_id, host_id=h001.id,
            timestamp=t1 + timedelta(minutes=i * 3),
            event_type=etype, severity=sev, title=title, description=desc,
            actor=actor, is_suspicious=sus,
        ))

    # HOST-002 events
    h002 = hosts[1]
    t2 = base_time + timedelta(minutes=20)
    sus_events_002 = [
        ("process_start", "high", "Suspicious updater started", "update.exe running from C:\\ProgramData", "update.exe", True),
        ("network_connect", "critical", "C2 HTTP beaconing", "update.exe → 93.184.216.34:8080 (60s interval)", "update.exe", True),
        ("persistence_created", "high", "Malicious scheduled task", "updater_task executes on boot", "update.exe", True),
        ("system_event", "warning", "New service installed", "DataSync service registered", "SYSTEM", True),
        ("network_connect", "high", "Exfil attempt detected", "Large outbound data transfer on port 8080", "update.exe", True),
    ]
    for i, (etype, sev, title, desc, actor, sus) in enumerate(sus_events_002):
        events.append(TimelineEvent(
            investigation_id=inv_id, host_id=h002.id,
            timestamp=t2 + timedelta(minutes=i * 4),
            event_type=etype, severity=sev, title=title, description=desc,
            actor=actor, is_suspicious=sus,
        ))

    # Normal events for HOST-003, HOST-005 (clean baseline)
    for host in [hosts[2], hosts[4]]:
        for i, (etype, sev, title) in enumerate([
            ("process_start", "info", "Nginx web server started"),
            ("network_connect", "info", "Routine DNS query"),
            ("system_event", "info", "Cron job executed"),
            ("authentication", "info", "SSH login from admin"),
            ("system_event", "info", "System update applied"),
            ("process_start", "info", "Backup agent started"),
        ]):
            events.append(TimelineEvent(
                investigation_id=inv_id, host_id=host.id,
                timestamp=base_time + timedelta(minutes=i * 10),
                event_type=etype, severity=sev, title=title,
                description=f"Routine {etype} event",
                actor="system", is_suspicious=False,
            ))

    events.sort(key=lambda e: e.timestamp)
    return events


async def _add_processes(db, inv_id, exec_id, host_id, is_sus, scenario, base_time):
    base = [
        (4, 0, "System", "C:\\Windows\\System32\\ntoskrnl.exe", "SYSTEM", 0.1, 12.0),
        (812, 4, "svchost.exe", "C:\\Windows\\System32\\svchost.exe", "SYSTEM", 0.2, 45.0),
        (2340, 812, "explorer.exe", "C:\\Windows\\explorer.exe", "user", 1.2, 85.0),
    ]
    if is_sus and scenario == "malware":
        base += [
            (9921, 812, "svch0st.exe", "C:\\Users\\user\\AppData\\Local\\Temp\\svch0st.exe", "user", 15.3, 95.0),
            (8834, 9921, "update.exe", "C:\\ProgramData\\update.exe", "user", 8.1, 42.0),
        ]
    elif is_sus and scenario == "c2":
        base += [
            (7721, 812, "update.exe", "C:\\ProgramData\\update.exe", "user", 8.1, 42.0),
        ]
    elif is_sus and scenario == "persistence":
        base += [
            (6612, 812, "svch0st.exe", "C:\\Users\\user\\AppData\\Local\\Temp\\svch0st.exe", "user", 15.3, 95.0),
        ]

    for pid, ppid, name, path, user, cpu, mem in base:
        sus = is_sus and name in ("svch0st.exe", "update.exe")
        p = ProcessRecord(
            execution_id=exec_id, host_id=host_id, investigation_id=inv_id,
            pid=pid, ppid=ppid, name=name, path=path, username=user,
            cpu_percent=cpu, memory_mb=mem, status="running",
            created_time=base_time + timedelta(minutes=random.randint(1, 30)),
            is_suspicious=sus,
        )
        db.add(p)


async def _add_network(db, inv_id, exec_id, host_id, is_sus, scenario):
    conns = [
        ("192.168.10.101", 52341, "8.8.8.8", 53, "UDP", "ESTABLISHED", None, "chrome.exe"),
        ("0.0.0.0", 3389, None, None, "TCP", "LISTEN", 812, "svchost.exe"),
    ]
    if is_sus and scenario == "malware":
        conns += [
            ("192.168.10.101", 44321, "185.220.101.47", 4444, "TCP", "ESTABLISHED", 9921, "svch0st.exe"),
        ]
    elif is_sus and scenario == "c2":
        conns += [
            ("192.168.10.102", 55001, "93.184.216.34", 8080, "TCP", "ESTABLISHED", 7721, "update.exe"),
        ]
    for local_ip, lp, remote_ip, rp, proto, state, pid, proc in conns:
        sus = is_sus and rp in (4444, 8080)
        n = NetworkConnection(
            execution_id=exec_id, host_id=host_id, investigation_id=inv_id,
            local_address=local_ip, local_port=lp,
            remote_address=remote_ip, remote_port=rp,
            protocol=proto, state=state, pid=pid, process_name=proc,
            is_suspicious=sus,
        )
        db.add(n)


async def _add_persistence(db, inv_id, exec_id, host_id, is_sus, scenario, base_time):
    items = [
        ("scheduled_task", "\\Microsoft\\Windows\\UpdateOrchestrator\\Schedule Scan",
         "Schedule Scan", "C:\\Windows\\System32\\UsoClient.exe StartScan", False),
    ]
    if is_sus and scenario == "malware":
        items += [
            ("registry_run", "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
             "Updater", "C:\\Users\\user\\AppData\\Local\\Temp\\svch0st.exe --persist", True),
            ("scheduled_task", "\\Microsoft\\Windows\\Maintenance\\updater_task",
             "updater_task", "C:\\ProgramData\\update.exe /silent", True),
        ]
    elif is_sus and scenario == "persistence":
        items += [
            ("service", "HKLM\\SYSTEM\\CurrentControlSet\\Services\\DataSync",
             "DataSync", "C:\\ProgramData\\DataSync\\agent.exe", True),
        ]
    for cat, loc, name, cmd, susp in items:
        p = PersistenceItem(
            execution_id=exec_id, host_id=host_id, investigation_id=inv_id,
            category=cat, location=loc, name=name, command=cmd, enabled=True,
            created_time=base_time + timedelta(minutes=random.randint(5, 60)),
            is_suspicious=susp,
        )
        db.add(p)


async def _add_events(db, inv_id, exec_id, host_id, is_sus, scenario, base_time):
    events = [
        (base_time, "Security", "authentication", 4624, "info", "Successful user logon", "winlogon.exe"),
        (base_time + timedelta(minutes=5), "System", "service_start", 7036, "info", "Service started", None),
    ]
    if is_sus:
        events += [
            (base_time + timedelta(minutes=15), "Security", "process_creation", 4688, "warning",
             "New process created in temp directory", "svch0st.exe"),
            (base_time + timedelta(minutes=16), "Security", "network_event", 5156, "critical",
             f"Outbound connection to threat actor IP detected", "svch0st.exe"),
            (base_time + timedelta(minutes=20), "Security", "registry_modification", 4657, "high",
             "HKCU Run key modified to point to malicious binary", "update.exe"),
        ]
    for ts, src, etype, eid, sev, msg, proc in events:
        e = EventLogRecord(
            execution_id=exec_id, host_id=host_id, investigation_id=inv_id,
            timestamp=ts, source=src, event_type=etype,
            event_id=eid, severity=sev, message=msg, user_name="user",
        )
        db.add(e)


if __name__ == "__main__":
    asyncio.run(seed_all())
