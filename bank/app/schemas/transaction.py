
from pydantic import BaseModel, Field
from datetime import datetime


class TransferCreate(BaseModel):
    from_account_id: int
    to_account_number: str
    amount: int = Field(gt=0, description="Amount in cents, must be greater than zero")


class TransactionOut(BaseModel):
    id: int
    account_id: int
    amount: int
    transaction_type: str
    transfer_id: str | None
    balance_after: int
    created_at: datetime

    class Config:
        from_attributes = True