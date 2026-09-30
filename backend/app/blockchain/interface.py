"""JOCKY Platform — Blockchain Provenance Interface"""
from abc import ABC, abstractmethod
from typing import Any


class BlockchainAdapter(ABC):
    """
    Interface for integrating blockchain backends (e.g. Ethereum, Hyperledger)
    for immutable evidence provenance tracking.
    """
    
    @abstractmethod
    async def record_provenance(
        self,
        case_id: str,
        merkle_root: str,
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Record a Merkle root on the blockchain.
        Returns transaction details (tx_hash, block, etc).
        """
        ...
        
    @abstractmethod
    async def verify_provenance(
        self,
        case_id: str,
        merkle_root: str
    ) -> dict[str, Any]:
        """
        Verify that a Merkle root exists on-chain for the given case.
        Returns verification status and transaction details if found.
        """
        ...
