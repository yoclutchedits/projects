
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.schemas.transaction import TransferCreate, TransactionOut
from app.routers.auth import get_current_user
from app.models.transactions import Transaction
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from app.utils.audit import log_action
router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/transfer")
def transfer_money(
    transfer_in: TransferCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_account = db.query(Account).filter(
        Account.id == transfer_in.from_account_id,
        Account.user_id == current_user.id
    ).with_for_update().first()
    if not from_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source account not found")


    DAILY_TRANSFER_LIMIT = 500000
    since = datetime.now(timezone.utc) - timedelta(days=1)
    total_sent_today = db.query(func.sum(Transaction.amount)).filter(
    Transaction.account_id == from_account.id,
    Transaction.amount < 0,
    Transaction.created_at >= since,
    ).scalar() or 0
    total_sent_today = abs(total_sent_today)


    if total_sent_today + transfer_in.amount > DAILY_TRANSFER_LIMIT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Daily transfer limit exceeded")

    VELOCITY_LIMIT_COUNT = 3
    VELOCITY_LIMIT_SECONDS = 60

    recent_window = datetime.now(timezone.utc) - timedelta(seconds=VELOCITY_LIMIT_SECONDS)

    recent_transfer_count = db.query(Transaction).filter(
        Transaction.account_id == from_account.id,
        Transaction.transaction_type == "transfer_debit",
        Transaction.created_at >= recent_window,
    ).count()

    if recent_transfer_count >= VELOCITY_LIMIT_COUNT:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many transfers in a short time. Please wait and try again.")
    to_account = db.query(Account).filter(
        Account.account_number == transfer_in.to_account_number
    ).with_for_update().first()

    if not to_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient account not found")

    if from_account.id == to_account.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot transfer to the same account")

    available_funds = from_account.balance + from_account.overdraft_limit
    if transfer_in.amount > available_funds:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")

    from_account.balance -= transfer_in.amount
    to_account.balance += transfer_in.amount
    shared_transfer_id = str(uuid.uuid4())
    debit_row = Transaction(
        account_id=from_account.id,
        amount=-transfer_in.amount,
        transaction_type="transfer_debit",
        transfer_id=shared_transfer_id,
        balance_after=from_account.balance,
    )
    credit_row = Transaction(
        account_id=to_account.id,
        amount=transfer_in.amount,
        transaction_type="transfer_credit",
        transfer_id=shared_transfer_id,
        balance_after=to_account.balance,
    )

    db.add(debit_row)
    db.add(credit_row)
    db.commit()
    db.refresh(debit_row)
    FLAG_THRESHOLD = 200000 

    if transfer_in.amount > FLAG_THRESHOLD:
        log_action(
            db=db,
            request=request,
            action="flagged_transfer",
            entity_type="transaction",
            entity_id=shared_transfer_id,
            user_id=current_user.id,
            changes={"amount": transfer_in.amount, "reason": "exceeds_flag_threshold"},
        )
        db.commit()

    return {"detail": "Transfer successful", "transfer_id": shared_transfer_id}