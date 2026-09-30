"""JOCKY Agent — Configuration"""
import os
import platform
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.agent",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    agent_id: str = "default-agent-id"
    server_url: str = "http://localhost:8000"
    api_key: str = "demo_agent_token"
    
    heartbeat_interval: int = 15
    poll_interval: int = 5
    
    # Platform info
    hostname: str = platform.node()
    platform_name: str = platform.system().lower()
    os_version: str = platform.platform()
    architecture: str = platform.machine()
    version: str = "1.0.0"


def get_settings() -> AgentSettings:
    # Try to read from agent_id file if it exists
    agent_id = "agent-" + platform.node().lower()
    
    settings = AgentSettings()
    if not os.environ.get("AGENT_ID"):
        settings.agent_id = agent_id
        
    return settings
