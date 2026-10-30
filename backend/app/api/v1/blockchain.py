from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.blockchain.blockchain_service import BlockchainService
from app.schemas.blockchain import BlockchainRegisterResponse, BlockchainVerifyResponse

router = APIRouter()


@router.post("/register/{report_id}", response_model=BlockchainRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_report_hash_on_chain(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Anchors the SHA-256 digest of a verified medical report onto the blockchain ledger.
    Zero patient personal information or clinical values are placed on-chain.
    """
    patient_id = current_user.patient_profile.id if current_user.patient_profile else current_user.id
    return BlockchainService.register_report_hash(db, patient_id=patient_id, report_id=report_id)


@router.get("/verify/{report_id}", response_model=BlockchainVerifyResponse)
def verify_report_integrity_against_chain(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Validates report integrity by bitwise comparison between current server disk file hash
    and the cryptographically anchored blockchain record.
    """
    patient_id = current_user.patient_profile.id if current_user.patient_profile else current_user.id
    return BlockchainService.verify_report_integrity(db, patient_id=patient_id, report_id=report_id)


@router.get("/audit-trail", response_model=List[BlockchainRegisterResponse])
def get_blockchain_audit_trail(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves chronological audit trail of anchored hashes.
    """
    return BlockchainService.get_audit_trail(db, limit=limit)
