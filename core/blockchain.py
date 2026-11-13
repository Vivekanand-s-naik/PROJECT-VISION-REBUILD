"""
ProjectVision Blockchain Audit Ledger.
Provides tamper-evident cryptographic SHA-256 verification of attendance records,
identity assertions, and security alerts.
"""

import time
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ProjectVision.Blockchain")

class Block:
    def __init__(self, index: int, previous_hash: str, timestamp: float, data: Any, block_hash: Optional[str] = None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.hash = block_hash if block_hash else self.calculate_hash()

    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block contents."""
        serialized_data = json.dumps(self.data, sort_keys=True)
        block_string = f"{self.index}{self.previous_hash}{self.timestamp:.6f}{serialized_data}"
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "formatted_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp)),
            "data": self.data,
            "hash": self.hash
        }


class Blockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """Create the initial block of the chain."""
        genesis_time = 1704067200.0  # Constant timestamp for consistent genesis
        genesis_block = Block(
            index=0,
            previous_hash="0" * 64,
            timestamp=genesis_time,
            data={"event": "ProjectVision Blockchain Genesis Block", "version": "2.0"}
        )
        self.chain.append(genesis_block)
        logger.info(f"Genesis block initialized with hash: {genesis_block.hash[:16]}...")

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, data: Any) -> Block:
        """Add a new block with the given data."""
        previous_block = self.get_latest_block()
        new_index = previous_block.index + 1
        new_timestamp = time.time()
        new_block = Block(
            index=new_index,
            previous_hash=previous_block.hash,
            timestamp=new_timestamp,
            data=data
        )
        self.chain.append(new_block)
        logger.debug(f"Added block #{new_index} with hash: {new_block.hash[:16]}...")
        return new_block

    def is_chain_valid(self) -> bool:
        """Verify the cryptographic integrity of the entire chain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Verify current hash matches its recalculated value
            if current.hash != current.calculate_hash():
                logger.error(f"Integrity check failed: Block #{current.index} hash mismatch.")
                return False

            # Verify chain linkage
            if current.previous_hash != previous.hash:
                logger.error(f"Integrity check failed: Block #{current.index} previous_hash mismatch.")
                return False

        return True

    def to_list(self) -> List[Dict[str, Any]]:
        return [block.to_dict() for block in self.chain]


class IdentityVerificationSystem:
    """High-level identity verification ledger."""

    def __init__(self):
        self.blockchain = Blockchain()

    def verify_identity(self, name: str, id_number: str, additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Record identity verification entry onto the blockchain."""
        entry = {
            "action": "IDENTITY_VERIFICATION",
            "name": name,
            "id_number": id_number,
            "status": "VERIFIED",
            "metadata": additional_info or {}
        }
        block = self.blockchain.add_block(entry)
        return block.to_dict()

    def record_attendance(self, student_id: str, student_name: str, status: str = "PRESENT", camera_id: str = "cam_1") -> Dict[str, Any]:
        """Record attendance punch into immutable ledger."""
        entry = {
            "action": "ATTENDANCE_RECORD",
            "student_id": student_id,
            "student_name": student_name,
            "status": status,
            "camera_id": camera_id
        }
        block = self.blockchain.add_block(entry)
        return block.to_dict()

    def record_security_event(self, event_type: str, camera_id: str, severity: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Record critical security alerts to prevent tampering."""
        entry = {
            "action": "SECURITY_ALERT",
            "event_type": event_type,
            "camera_id": camera_id,
            "severity": severity,
            "details": details
        }
        block = self.blockchain.add_block(entry)
        return block.to_dict()

    def get_records_by_id(self, id_number: str) -> List[Dict[str, Any]]:
        results = []
        for block in self.blockchain.chain:
            data = block.data
            if isinstance(data, dict):
                if data.get("id_number") == id_number or data.get("student_id") == id_number:
                    results.append(block.to_dict())
        return results

    def get_ledger(self) -> List[Dict[str, Any]]:
        return self.blockchain.to_list()


# Global identity blockchain instance
identity_ledger = IdentityVerificationSystem()

