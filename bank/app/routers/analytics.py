from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.transactions import Transaction
from app.routers.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/accounts/{account_id}/balance-history")
def balance_history(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    transactions = db.query(Transaction).filter(
        Transaction.account_id == account_id
    ).order_by(Transaction.created_at.asc()).all()

    history = [
        {"date": t.created_at.isoformat(), "balance": t.balance_after}
        for t in transactions
    ]

    return {"account_id": account_id, "history": history}


@router.get("/accounts/{account_id}/spending-breakdown")
def spending_breakdown(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    results = db.query(
        Transaction.transaction_type,
        func.sum(func.abs(Transaction.amount)).label("total")
    ).filter(
        Transaction.account_id == account.id
    ).group_by(Transaction.transaction_type).all()

    breakdown = [{"type": r.transaction_type, "total": r.total} for r in results]

    return {"account_id": account_id, "breakdown": breakdown}


@router.get("/accounts/{account_id}/statement")
def generate_statement(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    transactions = db.query(Transaction).filter(
        Transaction.account_id == account.id
    ).order_by(Transaction.created_at.asc()).all()

    file_path = f"/tmp/statement_{account.account_number}.pdf"

    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Statement for Account {account.account_number}", styles["Title"]))
    story.append(Paragraph(f"Account Type: {account.account_type.capitalize()}", styles["Normal"]))
    story.append(Paragraph(f"Current Balance: ${account.balance / 100:.2f}", styles["Normal"]))
    story.append(Spacer(1, 12))

    table_data = [["Date", "Type", "Amount", "Balance After"]]
    for t in transactions:
        table_data.append([
            t.created_at.strftime("%Y-%m-%d %H:%M"),
            t.transaction_type,
            f"${t.amount / 100:.2f}",
            f"${t.balance_after / 100:.2f}",
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(table)

    doc.build(story)

    return FileResponse(path=file_path, filename=f"statement_{account.account_number}.pdf", media_type="application/pdf")