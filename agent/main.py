"""JOCKY Agent — Main Entrypoint"""
import asyncio
import logging
import sys

from agent.config import get_settings
from agent.transport.client import AgentClient
from agent.runtime.ir_executor import IRExecutor
from agent.runtime.execution_context import ExecutionContext

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("jocky.agent")


async def agent_loop():
    settings = get_settings()
    logger.info(f"Starting JOCKY Agent {settings.version} on {settings.platform_name}")
    logger.info(f"Agent ID: {settings.agent_id}")
    
    client = AgentClient()
    
    # Try to register until successful
    while True:
        if client.register():
            break
        logger.warning("Registration failed. Retrying in 10s...")
        await asyncio.sleep(10)
        
    executor = IRExecutor(mode="live")
    
    poll_interval = settings.poll_interval
    heartbeat_interval = settings.heartbeat_interval
    
    last_heartbeat = 0.0
    
    while True:
        loop = asyncio.get_running_loop()
        now = loop.time()
        
        if now - last_heartbeat > heartbeat_interval:
            client.heartbeat()
            last_heartbeat = now
            
        jobs = client.poll_jobs()
        for job in jobs:
            job_id = job.get("job_id")
            logger.info(f"Received job {job_id}")
            
            try:
                ir = job.get("ir", {})
                if not ir:
                    logger.error(f"Job {job_id} has no IR payload.")
                    continue
                
                # Set up context
                context = ExecutionContext(
                    execution_id=job.get("execution_id", ""),
                    case_id=job.get("case_id", ""),
                    investigation_id=job.get("investigation_id", ""),
                    host_id=job.get("host_id", ""),
                    build_id=job.get("build_id", ""),
                    script_hash=job.get("script_hash", ""),
                )
                
                # Execute IR
                logger.info(f"Executing IR for job {job_id}...")
                result_ctx = executor.execute(ir, context=context)
                
                # Serialize and upload
                results = result_ctx.to_result()
                logger.info(f"Job {job_id} complete. Uploading {len(result_ctx.evidence)} evidence items.")
                client.submit_results(job_id, results)
                
            except Exception as e:
                logger.error(f"Job execution failed: {e}", exc_info=True)
                
        await asyncio.sleep(poll_interval)


def main():
    try:
        asyncio.run(agent_loop())
    except KeyboardInterrupt:
        logger.info("Agent shutting down.")


if __name__ == "__main__":
    main()
