
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserOut, UserLogin
from app.security import hash_password, verify_password, create_access_token
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.security import hash_password
from app.limiter import limiter
from fastapi.security import OAuth2PasswordBearer
from app.security import decode_access_token
from app.schemas.user import UpdateSettingsRequest
from app.models.token_blocklist import TokenBlocklist
from datetime import datetime, timezone
from fastapi import Request
from app.utils.audit import log_action
from datetime import timedelta
from app.models.verification_code import VerificationCode
from app.utils.account_utils import generate_verification_code
from app.utils.email import send_verification_email
from app.schemas.user import UserCreate, UserOut, UserLogin 
from app.schemas.user import VerifyEmailRequest
from app.schemas.user import Toggle2FARequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_pw = hash_password(user_in.password)

    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pw,
        full_name=user_in.full_name,
        is_active=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    code=generate_verification_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    verification = VerificationCode(
        user_id=new_user.id,
        code=code,
        expires_at=expires_at,
    )
    db.add(verification)
    db.commit()

    send_verification_email(new_user.email, code)


    return new_user


@router.post("/login")
@limiter.limit("5/minute")
def login(user_in: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()

    if not user or not verify_password(user_in.password, user.hashed_password):
        log_action(
            db=db, request=request, action="failed_login", entity_type="user",
            entity_id=user_in.email, user_id=user.id if user else None,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email before logging in")
    if not user.two_fa_enabled:
        # 2FA disabled -- issue the token immediately, same as before 2FA existed.
        access_token = create_access_token(data={"sub": str(user.id)})
        log_action(
            db=db, request=request, action="successful_login", entity_type="user",
            entity_id=str(user.id), user_id=user.id,
        )
        db.commit()
        return {"access_token": access_token, "token_type": "bearer"}
    code = generate_verification_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)  # hint: 2FA codes should be SHORT-lived -- much shorter than the 10-min signup code, since this happens every login

    two_fa_code = VerificationCode(
        user_id=user.id,
        code=code,
        expires_at=expires_at,
    )
    db.add(two_fa_code)
    db.commit()

    send_verification_email(user.email, code)

    log_action(
        db=db, request=request, action="password_verified", entity_type="user",
        entity_id=str(user.id), user_id=user.id,
    )
    db.commit()
    return {"detail": "Password correct. Check your email for a 2FA code."}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    jti = payload.get("jti")
    banned = db.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).first()
    if banned:
        raise credentials_exception

    user_id: str = payload.get("sub")

    if user_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    jti = payload.get("jti")
    exp = payload.get("exp")

    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

    blocked = TokenBlocklist(jti=jti, expires_at=expires_at)
    db.add(blocked)
    db.commit()

    return {"detail": "Successfully logged out"}

@router.post("/verify-email")
def verify_email(verify_in: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == verify_in.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    code_entry = db.query(VerificationCode).filter(
        VerificationCode.user_id == user.id,
        VerificationCode.code == verify_in.code,
        VerificationCode.used == False,
    ).first()

    if not code_entry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    if code_entry.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code expired")

    code_entry.used = True
    user.is_active = True
    db.commit()

    return {"detail": "Email verified successfully"}

@router.post("/login/verify-2fa")
def verify_2fa(verify_in: VerifyEmailRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == verify_in.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    code_entry = db.query(VerificationCode).filter(
        VerificationCode.user_id == user.id,
        VerificationCode.code == verify_in.code,
        VerificationCode.used == False,
    ).first()

    if not code_entry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    if code_entry.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code expired")

    code_entry.used = True

    access_token = create_access_token(data={"sub": str(user.id)})

    log_action(
        db=db, request=request, action="successful_login", entity_type="user",
        entity_id=str(user.id), user_id=user.id,
    )

    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/toggle-2fa")
def toggle_2fa(
    toggle_in: Toggle2FARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(toggle_in.password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    current_user.two_fa_enabled = toggle_in.enable
    db.commit()

    return {"detail": f"2FA has been {'enabled' if current_user.two_fa_enabled else 'disabled'}"}

@router.patch("/settings", response_model=UserOut)
def update_settings(
    settings_in: UpdateSettingsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if settings_in.full_name is not None:
        current_user.full_name = settings_in.full_name

    if settings_in.notify_large_transfer is not None:
        current_user.notify_large_transfer = settings_in.notify_large_transfer

    if settings_in.notify_failed_login is not None:
        current_user.notify_failed_login = settings_in.notify_failed_login

    db.commit()
    db.refresh(current_user)

    return current_user