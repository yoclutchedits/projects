
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.transactions import Transaction
from datetime import datetime, timezone, timedelta
import uuid
from app.models.scheduled_payment import ScheduledPayment
from app.utils.audit import log_action
def apply_monthly_interest(db: Session):
    savings_accounts = db.query(Account).filter(
        Account.account_type == "savings"
    ).all()
    results = []
    for account in savings_accounts:
        interest_amount = round(account.balance * account.interest_rate_bps / 10000 / 12)
        if interest_amount <= 0:
            continue
        account.balance += interest_amount
        interest_transaction = Transaction(
            account_id=account.id,
            amount=interest_amount,
            transaction_type="interest_credit",
            transfer_id=None,
            balance_after=account.balance,
        )
        db.add(interest_transaction)

        results.append({"account_id": account.id, "interest_applied": interest_amount})

    db.commit()
    return results
def process_due_payments(db: Session, request=None):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    due_payments = db.query(ScheduledPayment).filter(
        ScheduledPayment.next_run_at <= now,
        ScheduledPayment.is_active == True,
    ).all()

    results = []

    for payment in due_payments:
        from_account = db.query(Account).filter(Account.id == payment.from_account_id).with_for_update().first()
        to_account = db.query(Account).filter(Account.account_number == payment.to_account_number).with_for_update().first()

        if not from_account or not to_account:
            results.append({"payment_id": payment.id, "status": "failed", "reason": "account missing"})
            payment.next_run_at = payment.next_run_at + timedelta(days=payment.interval_days)
            continue

        available_funds = from_account.balance + from_account.overdraft_limit
        if payment.amount > available_funds:
            results.append({"payment_id": payment.id, "status": "failed", "reason": "insufficient funds"})
            payment.next_run_at = payment.next_run_at + timedelta(days=payment.interval_days)
            continue

        from_account.balance -= payment.amount
        to_account.balance += payment.amount
        shared_transfer_id = str(uuid.uuid4())

        db.add(Transaction(
            account_id=from_account.id, amount=-payment.amount,
            transaction_type="scheduled_payment_debit", transfer_id=shared_transfer_id,
            balance_after=from_account.balance,
        ))
        db.add(Transaction(
            account_id=to_account.id, amount=payment.amount,
            transaction_type="scheduled_payment_credit", transfer_id=shared_transfer_id,
            balance_after=to_account.balance,
        ))

        payment.next_run_at = payment.next_run_at + timedelta(days=payment.interval_days)

        results.append({"payment_id": payment.id, "status": "success", "transfer_id": shared_transfer_id})

    db.commit()
    return results