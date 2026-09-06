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
from app.routers import analytics
from app.models.scheduled_payment import ScheduledPayment
from fastapi.middleware.cors import CORSMiddleware
from app.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(analytics.router)
app.include_router(auth.router)
@app.get("/")
def root():
    return {"message": "Bank API is running"}