from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.users import User
from app.models.bills import Bill
from app.models.followed_bills import FollowedBill
from app.schemas.schemas import WatchlistOut
from app.core.security import jwt  # From security.py
from typing import List

router = APIRouter(prefix="/watchlist")

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401)
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401)
        return user
    except:
        raise HTTPException(status_code=401)

@router.post("/{bill_id}")
def follow_bill(bill_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if db.query(FollowedBill).filter(FollowedBill.user_id == user.id, FollowedBill.bill_id == bill_id).first():
        raise HTTPException(409, "Already following")
    followed = FollowedBill(user_id=user.id, bill_id=bill_id)
    db.add(followed)
    db.commit()
    return {"success": True}

@router.delete("/{bill_id}")
def unfollow_bill(bill_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    followed = db.query(FollowedBill).filter(FollowedBill.user_id == user.id, FollowedBill.bill_id == bill_id).first()
    if not followed:
        raise HTTPException(404)
    db.delete(followed)
    db.commit()
    return {"success": True}

@router.get("/", response_model=WatchlistOut)
def get_watchlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(FollowedBill).filter(FollowedBill.user_id == user.id).all()
    return {
        "watchlist": [
            {"bill_id": fb.bill_id, "title": fb.bill.title}
            for fb in items
        ]
    }