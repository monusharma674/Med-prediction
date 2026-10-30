from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class AdminStatsResponse(BaseModel):
    total_patients: int
    total_doctors: int
    total_reports: int
    total_predictions: int
    total_blockchain_records: int
    total_active_shares: int

    model_config = ConfigDict(from_attributes=True)


class AdminUserItem(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminAuditLogItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)
