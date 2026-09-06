
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.utils.audit import log_action
from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountOut
from app.utils.account_utils import generate_account_number
from app.routers.auth import get_current_user
from app.utils.scheduled_jobs import apply_monthly_interest
from app.utils.scheduled_jobs import process_due_payments



router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/", response_model=AccountOut)
def create_account(
    account_in: AccountCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_types = ["checking", "savings"]
    if account_in.account_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid account type")
    account_number = generate_account_number(db)
    if account_in.account_type == "checking":
        overdraft_limit = 50000   # $500.00 in cents
        interest_rate_bps = 0
    else:
        overdraft_limit = 0
        interest_rate_bps = 150  
    new_account = Account(
        user_id=current_user.id,
        account_number=account_number,
        account_type=account_in.account_type,
        balance=0,
        overdraft_limit=overdraft_limit,
        interest_rate_bps=interest_rate_bps,
    )

    db.add(new_account)
    log_action(
        db=db,
        request=request,
        action="create_account",
        entity_type="account",
        entity_id=account_number,   # we don't have new_account.id yet (not committed), so use the account_number instead
        user_id=current_user.id,
    )

    db.commit()
    db.refresh(new_account)

    return new_account
@router.get("/{account_id}", response_model=AccountOut)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    return account
@router.get("/", response_model=list[AccountOut])
def list_my_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    return accounts

@router.post("/run-interest-job")
def run_interest_job(db: Session = Depends(get_db)):
    results = apply_monthly_interest(db)
    return {"detail": "Interest job completed", "results": results}

@router.post("/run-scheduled-payments-job")
def run_scheduled_payments_job(db: Session = Depends(get_db)):
    results = process_due_payments(db)
    return {"detail": "Scheduled payments job completed", "results": results}