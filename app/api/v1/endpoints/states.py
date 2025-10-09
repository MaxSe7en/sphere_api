from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.db.session import get_db
from app.models import Bill, State
from app.schemas.schemas import StateBillCount

router = APIRouter()

@router.get("/", response_model=List[StateBillCount])
def get_states_with_bill_counts(db: Session = Depends(get_db)):
    results = (
        db.query(
            State.code.label("state"),
            State.name.label("name"),
            func.count(Bill.id).label("active_bills")
        )
        .outerjoin(Bill, (Bill.state == State.code) & (Bill.status > 0))
        .group_by(State.code, State.name)
        .order_by(State.code)
        .all()
    )
    return [StateBillCount(state=row.state, name=row.name, active_bills=row.active_bills) for row in results]
