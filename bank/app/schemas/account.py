
from pydantic import BaseModel
from datetime import datetime

class AccountCreate(BaseModel):
    account_type: str

class AccountOut(BaseModel):
    id: int
    account_number: str
    account_type: str
    balance: int
    overdraft_limit: int
    interest_rate_bps: int
    created_at: datetime

    class Config:
        from_attributes = True