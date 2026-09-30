"""JOCKY Agent — Transport Client"""
import httpx
import logging
from typing import Any

from agent.config import get_settings

logger = logging.getLogger("jocky.agent.transport")


class AgentClient:
    """Client for communicating with the JOCKY central server."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.server_url.rstrip("/")
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "X-Agent-ID": self.settings.agent_id,
            },
            timeout=30.0,
        )

    def register(self) -> bool:
        """Register the agent with the backend."""
        try:
            resp = self.client.post("/api/agents/register", json={
                "agent_id": self.settings.agent_id,
                "hostname": self.settings.hostname,
                "platform": self.settings.platform_name,
                "os_version": self.settings.os_version,
                "architecture": self.settings.architecture,
                "version": self.settings.version,
            })
            resp.raise_for_status()
            logger.info("Successfully registered with central server.")
            return True
        except Exception as e:
            logger.error(f"Failed to register: {e}")
            return False

    def heartbeat(self) -> bool:
        """Send a heartbeat to the backend."""
        try:
            resp = self.client.post("/api/agents/heartbeat", json={
                "agent_id": self.settings.agent_id,
                "status": "online",
            })
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.debug(f"Heartbeat failed: {e}")
            return False

    def poll_jobs(self) -> list[dict]:
        """Poll for pending jobs."""
        try:
            resp = self.client.get(f"/api/agents/jobs/{self.settings.agent_id}")
            resp.raise_for_status()
            data = resp.json()
            return data.get("jobs", [])
        except Exception as e:
            logger.error(f"Failed to poll jobs: {e}")
            return []

    def submit_results(self, job_id: str, results: dict) -> bool:
        """Submit job results to the backend."""
        try:
            resp = self.client.post("/api/agents/results", json={
                "agent_id": self.settings.agent_id,
                "job_id": job_id,
                "results": results,
            })
            resp.raise_for_status()
            logger.info(f"Successfully submitted results for job {job_id}.")
            return True
        except Exception as e:
            logger.error(f"Failed to submit results for job {job_id}: {e}")
            return False
