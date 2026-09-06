from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth
from app.models.user import User
from app.models.account import Account
from app.models.transactions import Transaction
from app.models.audit_logs import AuditLog
from app.models.token_blocklist import TokenBlocklist
from app.routers import transactions
from app.models.verification_code import VerificationCode
from app.routers import accounts
Base.metadata.create_all(bind=engine)
app = FastAPI()
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(auth.router)
@app.get("/")
def root():
    return {"message": "Bank API is running"}