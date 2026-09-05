from sqlalchemy import Column, Integer, String, DateTime, JSON ,ForeignKey
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False, index=True)  
    entity_type = Column(String, nullable=False, index=True) 
    entity_id = Column(String, nullable=False, index=True)   
    changes = Column(JSON, nullable=True)                 
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)