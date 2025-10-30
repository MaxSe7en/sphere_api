from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.users import User
from app.schemas.schemas import UserCreate, UserLogin, UserOut, Token
from app.core.security import verify_password, get_password_hash, create_access_token

router = APIRouter()
# router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email taken")
    hashed = get_password_hash(user_data.password)
    user = User(email=user_data.email, hashed_password=hashed, full_name=user_data.full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.email})
    return {"access_token": token}

@router.post("/login", response_model=Token)
def login(form_data: UserLogin, db: Session = Depends(get_db)):   # <-- UserLogin
    user = db.query(User).filter(User.email == form_data.email).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token}