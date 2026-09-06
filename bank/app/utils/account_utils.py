import random
from sqlalchemy.orm import Session
from app.models.account import Account

def generate_account_number(db: Session) -> str:
    while True:
        candidate = str(random.randint(1000000000, 9999999999))
        existing = db.query(Account).filter(Account.account_number == candidate).first()
        if not existing:
            return candidate