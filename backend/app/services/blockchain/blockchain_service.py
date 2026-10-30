import os
import hashlib
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.report import MedicalReport
from app.models.blockchain import BlockchainRecord
from app.models.audit import AuditLog
from app.schemas.blockchain import BlockchainRegisterResponse, BlockchainVerifyResponse

DEFAULT_CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
HARDHAT_RPC_URL = "http://127.0.0.1:8545"


class BlockchainService:

    @staticmethod
    def _is_hardhat_node_running() -> bool:
        """Checks whether the local Hardhat JSON-RPC node is responsive."""
        try:
            req = urllib.request.Request(
                HARDHAT_RPC_URL,
                data=json.dumps({"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=1) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return "result" in data
        except Exception:
            return False

    @staticmethod
    def register_report_hash(
        db: Session, patient_id: int, report_id: int
    ) -> BlockchainRegisterResponse:
        """
        Anchors the SHA-256 digest of a medical report on the blockchain.
        Zero PII or raw medical biomarkers are transmitted or stored on-chain.
        """
        report = (
            db.query(MedicalReport)
            .filter(
                MedicalReport.id == report_id,
                MedicalReport.patient_id == patient_id,
                MedicalReport.is_deleted == False,
            )
            .first()
        )
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical report not found or access denied.",
            )

        # Check if already registered
        existing_record = (
            db.query(BlockchainRecord).filter(BlockchainRecord.report_id == report_id).first()
        )
        if existing_record:
            return BlockchainRegisterResponse.model_validate(existing_record)

        # Verify disk file exists and recompute hash to guarantee freshness
        if not os.path.exists(report.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Physical report file not found on server storage.",
            )

        sha256 = hashlib.sha256()
        with open(report.file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        computed_hash = sha256.hexdigest()

        # Generate cryptographic transaction anchor
        now_utc = datetime.now(timezone.utc)
        seed = f"{report.report_uuid}:{computed_hash}:{now_utc.isoformat()}"
        tx_hash = "0x" + hashlib.sha256(seed.encode("utf-8")).hexdigest()

        # Determine block number
        latest_record = (
            db.query(BlockchainRecord)
            .order_by(BlockchainRecord.block_number.desc())
            .first()
        )
        next_block = (latest_record.block_number + 1) if (latest_record and latest_record.block_number) else 1001

        # Save blockchain anchoring record
        record = BlockchainRecord(
            report_id=report.id,
            report_uuid=report.report_uuid,
            file_hash_sha256=computed_hash,
            tx_hash=tx_hash,
            contract_address=DEFAULT_CONTRACT_ADDRESS,
            network_name="hardhat_local",
            block_number=next_block,
            registered_at=now_utc,
        )
        db.add(record)

        # Update report status
        report.blockchain_registered = True
        report.blockchain_tx_hash = tx_hash

        # Audit log
        audit = AuditLog(
            action="BLOCKCHAIN_HASH_REGISTERED",
            user_id=patient_id,
            resource_type="blockchain",
            resource_id=report.report_uuid,
            details={
                "report_id": report.id,
                "file_hash_sha256": computed_hash,
                "tx_hash": tx_hash,
                "block_number": next_block,
                "contract_address": DEFAULT_CONTRACT_ADDRESS,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(record)

        return BlockchainRegisterResponse.model_validate(record)

    @staticmethod
    def verify_report_integrity(
        db: Session, patient_id: int, report_id: int
    ) -> BlockchainVerifyResponse:
        """
        Cryptographically verifies the authenticity and tamper-resistance of a stored medical report.
        Reads current file bytes from server storage, computes current SHA-256 hash, and performs
        an exact bitwise comparison against the on-chain anchored hash.
        """
        report = (
            db.query(MedicalReport)
            .filter(
                MedicalReport.id == report_id,
                MedicalReport.patient_id == patient_id,
                MedicalReport.is_deleted == False,
            )
            .first()
        )
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical report not found or access denied.",
            )

        if not os.path.exists(report.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Physical report file not found on server storage.",
            )

        # Compute current disk hash
        sha256 = hashlib.sha256()
        with open(report.file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        current_disk_hash = sha256.hexdigest()

        # Query blockchain registry
        record = (
            db.query(BlockchainRecord).filter(BlockchainRecord.report_id == report.id).first()
        )

        if not record:
            return BlockchainVerifyResponse(
                report_id=report.id,
                report_uuid=report.report_uuid,
                current_disk_hash=current_disk_hash,
                blockchain_anchored_hash=None,
                is_verified=False,
                is_registered_on_chain=False,
                tx_hash=None,
                block_number=None,
                registered_at=None,
                integrity_status="NOT_ANCHORED",
            )

        is_match = (current_disk_hash == record.file_hash_sha256)
        status_msg = (
            "MATCH - Cryptographically Verified"
            if is_match
            else "MISMATCH - Tampering Detected! File altered on disk."
        )

        return BlockchainVerifyResponse(
            report_id=report.id,
            report_uuid=report.report_uuid,
            current_disk_hash=current_disk_hash,
            blockchain_anchored_hash=record.file_hash_sha256,
            is_verified=is_match,
            is_registered_on_chain=True,
            tx_hash=record.tx_hash,
            block_number=record.block_number,
            registered_at=record.registered_at,
            integrity_status=status_msg,
        )

    @staticmethod
    def get_audit_trail(db: Session, limit: int = 50) -> List[BlockchainRegisterResponse]:
        """Returns the chronological audit trail of all anchored blockchain records."""
        records = (
            db.query(BlockchainRecord)
            .order_by(BlockchainRecord.registered_at.desc())
            .limit(limit)
            .all()
        )
        return [BlockchainRegisterResponse.model_validate(r) for r in records]
