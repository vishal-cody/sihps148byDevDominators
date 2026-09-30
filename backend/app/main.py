"""JOCKY Platform — FastAPI Application Entry Point"""
import asyncio
import json
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import create_all_tables
from app.api import auth, investigations, jocky, hosts, agents, evidence, reports

settings = get_settings()

# ── WebSocket connection manager ──────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ── Application lifecycle ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_all_tables()
    if settings.seed_demo_data:
        try:
            from app.db.seed import seed_all
            await seed_all()
        except Exception as e:
            print(f"[WARN] Seed skipped: {e}")
    yield
    # Shutdown
    pass


# ── App factory ───────────────────────────────────────────────────────
app = FastAPI(
    title="JOCKY Platform API",
    description="Joint Cyber Operations & Knowledge Yielder — Forensic Investigation Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(investigations.router)
app.include_router(jocky.router)
app.include_router(hosts.router)
app.include_router(agents.router)
app.include_router(evidence.router)
app.include_router(reports.router)


# ── WebSocket ─────────────────────────────────────────────────────────
@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── Health check ──────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "JOCKY Platform", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "name": "JOCKY Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ── Broadcast helper (importable by services) ─────────────────────────
async def broadcast_event(event: dict):
    await manager.broadcast(event)
