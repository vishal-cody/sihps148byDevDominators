"""JOCKY Platform — Local Dev Blockchain Adapter"""
import hashlib
import time
import uuid
from typing import Any

from app.blockchain.interface import BlockchainAdapter


class LocalDevBlockchain(BlockchainAdapter):
    """
    Simulates a blockchain for local development and SIH demo purposes.
    Stores records in memory and simulates transaction latency/hashing.
    """
    
    def __init__(self):
        # In-memory "ledger"
        self._chain: list[dict] = []
        
    async def record_provenance(
        self,
        case_id: str,
        merkle_root: str,
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Simulate writing to chain."""
        tx_hash = hashlib.sha256(f"{case_id}{merkle_root}{time.time()}".encode()).hexdigest()
        
        record = {
            "tx_hash": tx_hash,
            "block_number": len(self._chain) + 1,
            "timestamp": time.time(),
            "case_id": case_id,
            "merkle_root": merkle_root,
            "metadata": metadata,
            "network": "local_dev_network",
        }
        self._chain.append(record)
        
        return {
            "status": "success",
            "tx_hash": tx_hash,
            "block_number": record["block_number"],
            "timestamp": record["timestamp"]
        }
        
    async def verify_provenance(
        self,
        case_id: str,
        merkle_root: str
    ) -> dict[str, Any]:
        """Simulate reading from chain."""
        # Find transaction
        for record in reversed(self._chain):
            if record["case_id"] == case_id and record["merkle_root"] == merkle_root:
                return {
                    "verified": True,
                    "tx_hash": record["tx_hash"],
                    "block_number": record["block_number"],
                    "timestamp": record["timestamp"],
                    "metadata": record["metadata"]
                }
                
        return {
            "verified": False,
            "reason": "Merkle root not found on-chain for this case ID."
        }


# Global instance for the backend
blockchain_adapter = LocalDevBlockchain()
