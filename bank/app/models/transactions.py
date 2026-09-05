from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    transaction_type = Column(String, nullable=False) 
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    transfer_id = Column(String, index=True, nullable=True)
    balance_after = Column(Integer, nullable=False)
    account = relationship("Account", back_populates="transactions")