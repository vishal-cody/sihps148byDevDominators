# JOCKY Platform — Implementation Baseline
## SIH26148 Pre-Implementation Audit
## Generated: 2026-09-28

---

## 1. Current Architecture

```
Frontend (React 19 / Vite / TS)  →  Backend (FastAPI / Python 3.11)  →  DB (SQLite dev / PostgreSQL prod)
                                           ↕
                                    Compiler (Python)
                                    Lexer → Parser → AST → Semantic → IR → Transformers
```

## 2. Existing Real Components

| Component | Status | Files |
|---|---|---|
| JOCKY Lexer (35 token types) | ✅ Real | `compiler/lexer.py` |
| JOCKY Parser (recursive descent) | ✅ Real | `compiler/parser.py` |
| JOCKY AST (12 node types, visitor) | ✅ Real | `compiler/ast_nodes.py` |
| Semantic Analyzer | ✅ Real | `compiler/semantic.py` |
| IR Builder | ✅ Real | `compiler/ir.py` |
| Transformation Engine (4 transforms, 3 profiles) | ✅ Real | `compiler/transformers/__init__.py` |
| JockyCompiler orchestrator | ✅ Real | `compiler/compiler.py` |
| FastAPI REST (7 routers, ~25 endpoints) | ✅ Real | `backend/app/api/` |
| JWT Auth + bcrypt + RBAC | ✅ Real | `backend/app/auth.py`, `backend/app/api/auth.py` |
| SQLAlchemy Models (14+ tables) | ✅ Real | `backend/app/models/` |
| Rule Engine (7 rules, MITRE mapped) | ✅ Real | `backend/app/analyzers/rule_engine.py` |
| Timeline Service | ✅ Real | `backend/app/services/timeline_service.py` |
| Graph Service (ReactFlow) | ✅ Real | `backend/app/services/graph_service.py` |
| Report Service (JSON, CSV) | ✅ Real | `backend/app/services/report_service.py` |
| React Frontend (10 pages) | ✅ Real | `frontend/src/pages/` |
| Monaco Editor IDE | ✅ Real | `frontend/src/pages/JockyStudio.tsx` |
| Compiler Tests (16) | ✅ Real | `compiler/tests/` |
| Docker Compose | ✅ Real | `docker-compose.yml` |
| WebSocket broadcast | ✅ Real | `backend/app/main.py` |
| Audit Logging | ✅ Real | `backend/app/models/user.py` (AuditLog) |

## 3. Existing Mock / Demo Components

| Component | Status | Location |
|---|---|---|
| All forensic evidence | ⚠️ Seeded | `backend/app/db/seed.py` (490 lines), `backend/app/services/investigation_service.py` |
| Investigation "execution" | ⚠️ Seeds data | `investigation_service.py:run_investigation_task()` |
| Agent registration | ⚠️ Creates DB record, returns `"demo_agent_token"` | `backend/app/api/agents.py` |
| Agent job polling | ⚠️ Returns `{"jobs": []}` always | `agents.py:poll_jobs()` |
| Agent result processing | ⚠️ `pass` stub | `investigation_service.py:process_agent_result()` |
| Security Resilience Lab | ⚠️ Frontend-only cards + setTimeout | `frontend/src/pages/Settings.tsx` |
| "Functional Equivalence: IDENTICAL" | ⚠️ Hardcoded string | `backend/app/api/jocky.py` |
| Host online/offline status | ⚠️ From seed data | `seed.py` |

## 4. Existing API Contracts

### Auth
- `POST /api/auth/login` — OAuth2 password form → JWT token
- `POST /api/auth/register` — admin-only user creation
- `GET /api/auth/me` — current user info

### Investigations
- `GET /api/investigations` — list (filterable by status)
- `GET /api/investigations/{id}` — detail with host/finding counts
- `POST /api/investigations` — create new investigation
- `POST /api/investigations/{id}/run` — run investigation (currently seeds demo data)
- `GET /api/investigations/stats` — aggregate stats

### JOCKY Compiler
- `POST /api/jocky/validate` — validate source → step results
- `POST /api/jocky/compile` — compile source → IR JSON
- `POST /api/jocky/build` — build with profile → SHA-256 artifact
- `POST /api/jocky/build/{id}/variant` — generate variant build
- `POST /api/jocky/scripts` — save script
- `GET /api/jocky/scripts` — list saved scripts
- `GET /api/jocky/builds` — list builds

### Hosts
- `GET /api/hosts` — list (filterable by status)
- `GET /api/hosts/{id}` — host detail
- `GET /api/hosts/stats` — aggregate counts

### Agents (stubs)
- `POST /api/agents/register` — register agent
- `POST /api/agents/heartbeat` — heartbeat update
- `GET /api/agents/jobs/{agent_id}` — poll jobs (returns empty)
- `POST /api/agents/results` — upload results (pass stub)

### Evidence
- `GET /api/evidence/{inv_id}/processes`
- `GET /api/evidence/{inv_id}/network`
- `GET /api/evidence/{inv_id}/persistence`
- `GET /api/timeline/{inv_id}`
- `GET /api/findings/{inv_id}`
- `GET /api/graph/{inv_id}`

### Reports
- `POST /api/reports/{inv_id}` — generate report
- `GET /api/reports/{inv_id}` — list reports
- `GET /api/reports/download/{report_id}` — download

## 5. Existing Database Models

| Table | Key Columns | Foreign Keys |
|---|---|---|
| `users` | id, username, email, hashed_password, role, is_active | — |
| `audit_logs` | id, user_id, action, resource, source_ip, result | users.id |
| `hosts` | id, hostname, ip_address, os_type, status, is_demo | — |
| `agents` | id, host_id, agent_key, version, platform, status | hosts.id |
| `investigations` | id, case_id, name, status, priority, assigned_hosts, jocky_script_id | users.id |
| `executions` | id, investigation_id, host_id, status, build_id | investigations.id |
| `jocky_scripts` | id, name, source_code, created_by, is_valid | — |
| `jocky_builds` | id, script_id, profile, sha256_hash, ir_json, transformation_log | — |
| `processes` | id, execution_id, host_id, investigation_id, pid, ppid, name, path, ... | executions.id |
| `network_connections` | id, execution_id, host_id, investigation_id, local/remote addr/port, ... | executions.id |
| `persistence_items` | id, execution_id, host_id, investigation_id, category, location, ... | executions.id |
| `event_logs` | id, execution_id, host_id, investigation_id, timestamp, source, ... | executions.id |
| `filesystem_events` | id, execution_id, host_id, investigation_id, path, event_type, ... | executions.id |
| `findings` | id, investigation_id, host_id, title, severity, mitre_technique, ... | investigations.id |
| `timeline_events` | id, investigation_id, host_id, timestamp, event_type, ... | investigations.id |
| `indicators` | id, investigation_id, indicator_type, value, is_ioc | — |
| `reports` | id, investigation_id, format, filename, file_path, status | investigations.id |

## 6. Existing JOCKY Syntax

```jocky
investigation "Name" {
    collect <target>
    analyze <target>
    filter <target> where <field> <op> <value>
    filter <target> where <field> in [<values>]
    generate timeline
    generate report
}

host "HOSTNAME" {
    collect <target>
    filter <target> where <condition>
    generate report
}
```

### Collector Targets
`processes`, `network_connections`, `system_info`, `event_logs`, `persistence`, `filesystem`, `startup_items`, `browser_artifacts`, `hashes`

## 7. Existing IR Schema

```json
{
  "version": "1.0",
  "type": "ir_program",
  "generated_at": "ISO timestamp",
  "scopes": [
    {
      "scope_type": "investigation | host",
      "name": "string",
      "operations": [
        {
          "op": "COLLECT | ANALYZE | FILTER | GENERATE_TIMELINE | GENERATE_REPORT",
          "target": "PROCESSES | NETWORK_CONNECTIONS | ...",
          "arguments": {}
        }
      ]
    }
  ]
}
```

## 8. Current Limitations (Migration Targets)

1. IR compiled but never executed — investigation seeds demo data
2. No real endpoint agent
3. All evidence is hardcoded
4. Security Resilience Lab is frontend mock
5. Functional equivalence is hardcoded string
6. Agent APIs are stubs
7. Redis configured but unused
8. No evidence hashing
9. No blockchain provenance
10. No cross-platform collectors

## 9. Planned Migration Path

### P0 — Core Execution
1. Formalize IR spec (`docs/FORENSIC_IR_SPEC.md`)
2. Build IR Execution Engine (`backend/app/runtime/`)
3. Build real agent (`agent/`)
4. Implement 4 collectors (process, network, system, filesystem)
5. Windows + Linux platform adapters

### P1 — Evidence Integrity
6. Evidence hashing + provenance (`backend/app/services/provenance/`)
7. Blockchain provenance (`backend/app/blockchain/`)
8. Real multi-host orchestration (job dispatch)
9. Semantic equivalence verifier
10. Policy/capability engine

### P2 — Analysis & Demo
11. Cross-host correlation
12. Security compatibility lab (real measurements)
13. Language improvements (variables, functions)
14. Reporting improvements
15. Testing + documentation
