
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_number = Column(String, unique=True, index=True, nullable=False)
    account_type = Column(String, nullable=False)
    balance = Column(Integer, default=0, nullable=False)
    overdraft_limit = Column(Integer, default=0, nullable=False)
    interest_rate_bps = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    owner = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")