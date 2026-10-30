from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BlockchainRegisterResponse(BaseModel):
    report_id: int
    report_uuid: str
    file_hash_sha256: str
    tx_hash: str
    contract_address: str
    network_name: str
    block_number: int
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlockchainVerifyResponse(BaseModel):
    report_id: int
    report_uuid: str
    current_disk_hash: str
    blockchain_anchored_hash: Optional[str] = None
    is_verified: bool
    is_registered_on_chain: bool
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    registered_at: Optional[datetime] = None
    integrity_status: str

    model_config = ConfigDict(from_attributes=True)
