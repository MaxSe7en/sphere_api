# routers/bills.py (Rewritten to handle full parsing, update detection with change_hash, and sub-models)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models import Bill, BillHistory
from app.schemas import schemas

router = APIRouter()

@router.get("/{bill_id}", response_model=schemas.Bill)
async def get_bill(bill_id: str, db: Session = Depends(get_db)):
    db_bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not db_bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return db_bill

@router.get("/state/{state}", response_model=schemas.PaginatedBills)
def get_state_bills(
    state: str,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    # Subquery for latest history per bill
    subq = (
        db.query(
            BillHistory.bill_id,
            func.max(BillHistory.date).label("latest_date")
        )
        .group_by(BillHistory.bill_id)
        .subquery()
    )

    query = (
        db.query(
            Bill,
            BillHistory.date.label("last_action_date"),
            BillHistory.action.label("last_action"),
        )
        .outerjoin(subq, Bill.id == subq.c.bill_id)
        .outerjoin(
            BillHistory,
            (BillHistory.bill_id == subq.c.bill_id) &
            (BillHistory.date == subq.c.latest_date)
        )
        .filter(Bill.state == state.upper())
    )

    total = query.count()
    rows = query.offset(offset).limit(limit).all()

    bills_out = []
    for bill, last_date, last_action in rows:
        bill_dict = schemas.BillOut.from_orm(bill).dict()
        bill_dict["last_action_date"] = last_date
        bill_dict["last_action"] = last_action
        bills_out.append(bill_dict)

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "next_offset": offset + limit if offset + limit < total else None,
        "prev_offset": offset - limit if offset - limit >= 0 else None,
        "bills": bills_out,
    }
