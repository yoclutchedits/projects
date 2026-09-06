
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserOut, UserLogin
from app.security import hash_password, verify_password, create_access_token
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.security import hash_password
from fastapi.security import OAuth2PasswordBearer
from app.security import decode_access_token
from app.models.token_blocklist import TokenBlocklist
from datetime import datetime, timezone
from fastapi import Request
from app.utils.audit import log_action


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
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login")
def login(user_in: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()

    if not user or not verify_password(user_in.password, user.hashed_password):
        log_action(
            db=db,
            request=request,
            action="failed_login",
            entity_type="user",
            entity_id=user_in.email,
            user_id=user.id if user else None,   
        )
        db.commit()  

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Log the SUCCESSFUL attempt.
    log_action(
        db=db,
        request=request,
        action="successful_login",
        entity_type="user",
        entity_id=str(user.id),
        user_id=user.id,
    )

    access_token = create_access_token(data={"sub": str(user.id)})
    db.commit()   

    return {"access_token": access_token, "token_type": "bearer"}

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

    # Hint: exp comes back from the JWT payload as a raw number
    # (seconds since 1970 — a "unix timestamp"), not a datetime object.
    # We need to convert it into a real datetime to store in our
    # DateTime column. fromtimestamp(..., tz=timezone.utc) does this.
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

    blocked = TokenBlocklist(jti=jti, expires_at=expires_at)
    db.add(blocked)
    db.commit()

    return {"detail": "Successfully logged out"}