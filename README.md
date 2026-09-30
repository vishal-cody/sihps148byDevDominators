# JOCKY — Joint Cyber Operations & Knowledge Yielder
### SIH 2025 Problem Statement 26148

<div align="center">

![JOCKY Platform](https://img.shields.io/badge/JOCKY-Forensic%20Platform-blue?style=for-the-badge&logo=shield)
![SIH 2025](https://img.shields.io/badge/SIH-2025%20PS%2026148-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)

**A cross-platform forensic programming language and investigation platform**  
*Written for Smart India Hackathon 2025 — Problem Statement 26148*

</div>

---

## ⚠ Security Disclaimer

> **JOCKY Platform is a forensic investigation tool designed for authorized use only.**
> 
> The "Security Resilience Lab" demonstrates concepts via **controlled simulation only**.
> No real EDR disabling, antivirus bypass, kernel manipulation, credential theft,
> process hollowing, reflective injection, API unhooking, or security product tampering
> is implemented. The IR transformation engine uses only safe, semantic-preserving
> code transformations (identifier renaming, operation reordering, constant representation).

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    JOCKY Platform                         │
│                                                          │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │  JOCKY       │    │   Frontend (React/Vite/TS)   │   │
│  │  Studio      │◄───►  Dashboard / Studio / Graph  │   │
│  │  (Monaco)    │    └──────────────┬───────────────┘   │
│  └──────────────┘                   │ REST + WebSocket   │
│                                     ▼                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │            FastAPI Backend                        │   │
│  │  Auth │ Investigations │ Evidence │ Reports       │   │
│  │  ┌────────────┐  ┌───────────────────────────┐  │   │
│  │  │  JOCKY     │  │  Investigation Engine      │  │   │
│  │  │  Compiler  │  │  RuleEngine │ Timeline     │  │   │
│  │  │  Lexer→IR  │  │  Findings   │ Graph        │  │   │
│  │  └────────────┘  └───────────────────────────┘  │   │
│  └──────────────────────────┬───────────────────────┘   │
│                              │                           │
│          ┌───────────────────┼───────────────────┐      │
│          ▼                   ▼                   ▼      │
│     PostgreSQL            Redis              Agent(s)   │
│     (evidence DB)         (pub/sub)          Python     │
│                                              Collectors  │
└──────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Docker (Recommended)

```bash
# Clone repository
git clone <repo>
cd jocky

# Copy env file
cp .env.example .env

# Start everything
docker compose up --build

# Open browser
open http://localhost:5173

# Login: admin / admin123
```

### Local Development

```bash
# Install all dependencies
make install

# Start dev servers
make dev

# Backend:  http://localhost:8000
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

---

## JOCKY Language Syntax

JOCKY (`.jky`) is a domain-specific language for defining forensic investigation workflows.

### Investigation Block

```jocky
investigation "Enterprise Security Sweep" {
    // Collect forensic evidence
    collect system_info
    collect processes
    collect network_connections
    collect persistence
    collect event_logs
    collect filesystem

    // Analyze collected data
    analyze processes
    analyze network_connections

    // Apply filters
    filter processes where cpu > 10
    filter network_connections where port in [4444, 1337, 8080]

    // Generate outputs
    generate timeline
    generate report
}
```

### Host Block

```jocky
host "HOST-001" {
    collect processes
    collect network_connections
    filter processes where cpu > 50
    generate report
}
```

### Grammar Summary

| Keyword | Syntax | Description |
|---------|--------|-------------|
| `investigation` | `investigation "Name" { ... }` | Define investigation scope |
| `host` | `host "Name" { ... }` | Target specific host |
| `collect` | `collect <target>` | Collect forensic data |
| `analyze` | `analyze <target>` | Run analysis on data |
| `filter` | `filter <target> where <condition>` | Filter collected data |
| `generate` | `generate timeline\|report` | Generate output |

### Collector Targets

| Target | Description |
|--------|-------------|
| `processes` | Running process list with hashes |
| `network_connections` | Active TCP/UDP connections |
| `system_info` | OS, hardware, user info |
| `event_logs` | Windows Event Log / Linux journal |
| `persistence` | Registry, scheduled tasks, services |
| `filesystem` | File system artifacts |
| `browser_artifacts` | Browser history, cache |
| `hashes` | File hash computation |

---

## Components

### 1. JOCKY Compiler Pipeline

```
Source (.jky)
    ↓ Lexer        — tokenizes JOCKY source
    ↓ Parser       — recursive-descent, produces AST
    ↓ AST          — typed node hierarchy
    ↓ Semantic     — validates targets, fields, scopes
    ↓ IR Builder   — produces JOCKY IR (JSON-serializable)
    ↓ Transformer  — applies build profile transformations
    ↓ Build Output — SHA-256 signed IR artifact
```

### 2. IR Transformation Engine (Build Diversification)

| Transformation | Description |
|---------------|-------------|
| Identifier Renaming | `COLLECT → ENUM`, `ANALYZE → INSPECT` |
| Operation Reordering | Reorders independent collect ops |
| Constant Representation | Integers → hex equivalents |
| Metadata Variation | UUID/timestamp per build |
| Profile Selection | `standard`, `hardened`, `variant` |

### 3. Forensic Collectors

| Collector | Windows | Linux |
|-----------|---------|-------|
| ProcessCollector | ✓ | ✓ |
| NetworkCollector | ✓ | ✓ |
| SystemInfoCollector | ✓ | ✓ |
| EventLogCollector | ✓ | ✓ (journal) |
| PersistenceCollector | ✓ | ✓ (systemd/cron) |
| FilesystemCollector | ✓ | ✓ |

### 4. Investigation Engine

- **Rule Engine**: YAML-defined detection rules with MITRE ATT&CK mapping
- **Timeline Service**: Merges all evidence sources chronologically
- **Graph Service**: Builds React Flow compatible evidence graph
- **Report Generator**: JSON/CSV/PDF forensic reports

---

## API Documentation

Full OpenAPI documentation at: `http://localhost:8000/docs`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Authenticate, get JWT |
| `GET` | `/api/investigations` | List investigations |
| `POST` | `/api/investigations` | Create investigation |
| `POST` | `/api/investigations/{id}/run` | Dispatch investigation |
| `POST` | `/api/jocky/validate` | Validate JOCKY script |
| `POST` | `/api/jocky/compile` | Compile to IR |
| `POST` | `/api/jocky/build` | Build with profile |
| `POST` | `/api/jocky/build/{id}/variant` | Generate variant build |
| `GET` | `/api/hosts` | List all hosts |
| `GET` | `/api/timeline/{inv_id}` | Get investigation timeline |
| `GET` | `/api/findings/{inv_id}` | Get rule-based findings |
| `GET` | `/api/graph/{inv_id}` | Get evidence graph |
| `POST` | `/api/reports/{inv_id}` | Generate report |

---

## SIH Demo Script

### Step 1: Dashboard

- Open `http://localhost:5173`
- Login as `admin / admin123`
- Show: 24 online hosts, 6 investigations, 11 high findings

### Step 2: JOCKY Studio

- Navigate to `/jocky`
- Show the pre-loaded "Enterprise Sweep" script

### Step 3: Validate

- Click **Validate**
- Show pipeline: Lexer ✓ → Parser ✓ → AST ✓ → Semantic ✓

### Step 4: Build & Variant

- Click **Build** → shows Build A with SHA-256
- Click **Generate Variant** → shows Build B with different SHA-256
- Show **Functional Equivalence: IDENTICAL**

### Step 5: Deploy Investigation

- Navigate to `/investigations`
- Open `INV-2025-001`
- Show 5 hosts, click **Run** 

### Step 6: Timeline

- Navigate to `/timeline`
- Filter by `suspicious` only
- Show critical C2 connection events

### Step 7: Evidence Graph

- Navigate to `/graph`
- Show red suspicious nodes: `svch0st.exe → 185.220.101.47:4444`

### Step 8: Findings

- Navigate to `/findings`
- Show finding cards with MITRE ATT&CK mapping, confidence bars

### Step 9: Report

- Navigate to `/reports`
- Select investigation → Generate JSON report → Download

### Step 10: Security Resilience Lab

- Navigate to `/settings`
- Run "EDR Interference Simulation"
- Show: Traditional tool BLOCKED, JOCKY ALLOWED

---

## Security Limitations

This platform is **research and education software for authorized forensic use**:

1. ❌ No EDR disabling
2. ❌ No antivirus bypass  
3. ❌ No kernel manipulation
4. ❌ No credential theft
5. ❌ No reflective injection
6. ❌ No process hollowing
7. ❌ No API unhooking
8. ❌ No direct syscall evasion
9. ❌ No BYOVD exploitation
10. ✅ Safe read-only forensic collection
11. ✅ Semantic-preserving IR transformations only

---

## Future Roadmap

- [ ] LLVM backend for JOCKY IR (LLVM bitcode generation)
- [ ] Full mTLS agent communication
- [ ] Live EDR telemetry integration (YARA, Sigma rules)
- [ ] MITRE ATT&CK Navigator integration
- [ ] Memory forensics (Volatility integration)
- [ ] Network PCAP analysis
- [ ] Multi-tenant investigation isolation
- [ ] Real-time WebSocket investigation updates
- [ ] JOCKY Language Server Protocol (LSP)
- [ ] Mobile app for investigation monitoring

---

## Project Structure

```
jocky/
├── frontend/          React + Vite + TypeScript + Tailwind
│   └── src/
│       ├── pages/     Dashboard, Studio, Timeline, Graph, Findings...
│       ├── components/
│       ├── services/  Typed API client
│       └── contexts/  Auth context
├── backend/           Python + FastAPI
│   └── app/
│       ├── api/       REST endpoints
│       ├── models/    SQLAlchemy models
│       ├── services/  Investigation, Timeline, Graph, Report
│       ├── analyzers/ Rule-based detection engine
│       └── db/        Seeder (INV-2025-001)
├── compiler/          JOCKY compiler pipeline
│   ├── lexer.py       Tokenizer
│   ├── parser.py      Recursive-descent parser
│   ├── ast_nodes.py   AST node dataclasses
│   ├── semantic.py    Semantic analyzer
│   ├── ir.py          JOCKY IR + builder
│   ├── transformers/  Build diversification engine
│   └── compiler.py    Main orchestrator
├── agent/             Python forensic agent (TODO: Phase 9)
├── scenarios/         Demo data scenarios
├── docker-compose.yml Full stack Docker setup
├── Makefile           Developer convenience commands
└── .env.example       Environment variable template
```

---

*Built for Smart India Hackathon 2025 — Problem Statement 26148*  
*"Creation of scripts/functions with new programming language to commence Computer & Network forensic analysis without triggering security solutions"*
