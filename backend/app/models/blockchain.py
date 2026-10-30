from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database.session import Base


class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("medical_reports.id", ondelete="CASCADE"), unique=True, nullable=False)

    report_uuid = Column(String(64), index=True, nullable=False)
    file_hash_sha256 = Column(String(64), index=True, nullable=False)
    tx_hash = Column(String(128), unique=True, nullable=False)
    contract_address = Column(String(64), nullable=False)
    network_name = Column(String(50), default="hardhat_local", nullable=False)
    block_number = Column(Integer, nullable=True)

    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    report = relationship("MedicalReport", back_populates="blockchain_record")
