"""JOCKY Platform — Evidence Graph Service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.evidence import ProcessRecord, NetworkConnection, PersistenceItem
from app.models.host import Host


async def build_evidence_graph(investigation_id: str, db: AsyncSession) -> dict:
    """Build a React Flow compatible node/edge graph from evidence."""
    nodes = []
    edges = []
    seen_nodes = set()

    def add_node(node_id: str, label: str, node_type: str, data: dict = None, suspicious: bool = False):
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            color_map = {
                "host": "#3b82f6",
                "process": "#8b5cf6",
                "ip": "#ef4444" if suspicious else "#10b981",
                "persistence": "#f59e0b",
                "file": "#6366f1",
                "user": "#06b6d4",
            }
            nodes.append({
                "id": node_id,
                "type": "forensicNode",
                "data": {
                    "label": label,
                    "nodeType": node_type,
                    "color": color_map.get(node_type, "#64748b"),
                    "suspicious": suspicious,
                    **(data or {}),
                },
                "position": {"x": 0, "y": 0},  # frontend layouts
            })

    def add_edge(source: str, target: str, label: str, suspicious: bool = False):
        edge_id = f"{source}-{target}-{label}"
        edges.append({
            "id": edge_id,
            "source": source,
            "target": target,
            "label": label,
            "type": "smoothstep",
            "style": {"stroke": "#ef4444" if suspicious else "#64748b"},
            "animated": suspicious,
        })

    # Get distinct hosts
    hosts_q = await db.execute(
        select(ProcessRecord.host_id).where(
            ProcessRecord.investigation_id == investigation_id
        ).distinct()
    )
    host_ids = [r[0] for r in hosts_q.all()]

    for host_id in host_ids:
        hq = await db.execute(select(Host).where(Host.id == host_id))
        host = hq.scalar_one_or_none()
        hostname = host.hostname if host else host_id[:8]
        add_node(f"host_{host_id}", hostname, "host")

        # Processes
        pq = await db.execute(
            select(ProcessRecord).where(
                ProcessRecord.investigation_id == investigation_id,
                ProcessRecord.host_id == host_id,
            )
        )
        for proc in pq.scalars().all():
            proc_node = f"proc_{proc.pid}_{host_id}"
            add_node(proc_node, f"{proc.name}\nPID:{proc.pid}", "process",
                     {"pid": proc.pid, "path": proc.path}, proc.is_suspicious)
            add_edge(f"host_{host_id}", proc_node, "runs", proc.is_suspicious)

            # Parent-child
            if proc.ppid and proc.ppid != proc.pid:
                parent_node = f"proc_{proc.ppid}_{host_id}"
                if parent_node in seen_nodes:
                    add_edge(parent_node, proc_node, "spawned", proc.is_suspicious)

        # Network connections
        nq = await db.execute(
            select(NetworkConnection).where(
                NetworkConnection.investigation_id == investigation_id,
                NetworkConnection.host_id == host_id,
                NetworkConnection.remote_address.isnot(None),
            )
        )
        for conn in nq.scalars().all():
            ip_node = f"ip_{conn.remote_address}"
            add_node(ip_node, f"{conn.remote_address}:{conn.remote_port}", "ip",
                     {"protocol": conn.protocol}, conn.is_suspicious)
            src_node = f"proc_{conn.pid}_{host_id}" if conn.pid else f"host_{host_id}"
            add_edge(src_node, ip_node, "connected_to", conn.is_suspicious)

        # Persistence
        peq = await db.execute(
            select(PersistenceItem).where(
                PersistenceItem.investigation_id == investigation_id,
                PersistenceItem.host_id == host_id,
            )
        )
        for item in peq.scalars().all():
            persist_node = f"persist_{item.id}"
            add_node(persist_node, f"{item.category}\n{item.name}", "persistence",
                     {"location": item.location}, item.is_suspicious)
            add_edge(f"host_{host_id}", persist_node, "persistence", item.is_suspicious)

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "suspicious_nodes": sum(1 for n in nodes if n["data"].get("suspicious")),
        }
    }
