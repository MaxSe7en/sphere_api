# routers/bills.py (Rewritten to handle full parsing, update detection with change_hash, and sub-models)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models import Bill, BillHistory
from app.schemas import schemas
from app.services.legiscan_service import legiscan
from app.schemas.schemas import PaginatedBills, BillListItem
from datetime import datetime
from app.services.ai_service import generate_bill_ai

router = APIRouter()

@router.get("/{bill_id}", response_model=schemas.Bill)
async def get_bill(bill_id: str, db: Session = Depends(get_db)):
    db_bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not db_bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return db_bill

# @router.get("/state/{state}", response_model=schemas.PaginatedBills)
# def get_state_bills(
#     state: str,
#     limit: int = Query(100, ge=1, le=200),
#     offset: int = Query(0, ge=0),
#     db: Session = Depends(get_db)
# ):
#     # Subquery for latest history per bill
#     subq = (
#         db.query(
#             BillHistory.bill_id,
#             func.max(BillHistory.date).label("latest_date")
#         )
#         .group_by(BillHistory.bill_id)
#         .subquery()
#     )

#     query = (
#         db.query(
#             Bill,
#             BillHistory.date.label("last_action_date"),
#             BillHistory.action.label("last_action"),
#         )
#         .outerjoin(subq, Bill.id == subq.c.bill_id)
#         .outerjoin(
#             BillHistory,
#             (BillHistory.bill_id == subq.c.bill_id) &
#             (BillHistory.date == subq.c.latest_date)
#         )
#         .filter(Bill.state == state.upper())
#     )

#     total = query.count()
#     rows = query.offset(offset).limit(limit).all()

#     bills_out = []
#     for bill, last_date, last_action in rows:
#         bill_dict = schemas.BillOut.from_orm(bill).dict()
#         bill_dict["last_action_date"] = last_date
#         bill_dict["last_action"] = last_action
#         bills_out.append(bill_dict)

#     return {
#         "total": total,
#         "limit": limit,
#         "offset": offset,
#         "next_offset": offset + limit if offset + limit < total else None,
#         "prev_offset": offset - limit if offset - limit >= 0 else None,
#         "bills": bills_out,
#     }


@router.post("/sync/{state}")
async def sync_state_bills(state: str, db: Session = Depends(get_db)):
    """🔄 SYNC: Fetch + Save MasterList to DB (change_hash delta)"""
    masterlist = await legiscan.get_master_list(state)
    
    updated = 0
    for bill_id_str, data in masterlist.items():
        if not isinstance(data, dict) or 'bill_id' not in data:
            continue
            
        bill_id = int(bill_id_str)
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        
        if bill and bill.change_hash == data.get('change_hash'):
            continue  # ✅ No change
            
        bill_data = {
            'id': bill_id,
            'state': state.upper(),
            'bill_number': data.get('number'),
            'change_hash': data.get('change_hash'),
            'title': data.get('title'),
            'description': data.get('description'),
            'url': data.get('url'),
            'status': data.get('status'),
            'status_date': datetime.strptime(data['status_date'], '%Y-%m-%d') if data.get('status_date') else None,
            'last_updated': datetime.strptime(data['last_action_date'], '%Y-%m-%d') if data.get('last_action_date') else None,
        }
        
        if not bill:
            bill = Bill(**bill_data)
            db.add(bill)
        else:
            for k, v in bill_data.items():
                setattr(bill, k, v)
        
        updated += 1
    
    db.commit()
    return {"state": state, "synced": len(masterlist), "updated": updated}

@router.get("/state/{state}", response_model=PaginatedBills)
def get_state_bills(
    state: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """📋 BillFeed: Paginated + Last Action"""
    subq = (
        db.query(BillHistory.bill_id, func.max(BillHistory.date).label("latest_date"))
        .filter(BillHistory.bill_id == Bill.id)  # Correlate
        .group_by(BillHistory.bill_id)
        .subquery()
    )
    
    query = (
        db.query(Bill, BillHistory.date.label("last_action_date"), BillHistory.action.label("last_action"))
        .outerjoin(subq, Bill.id == subq.c.bill_id)
        .outerjoin(
            BillHistory,
            (BillHistory.bill_id == subq.c.bill_id) & (BillHistory.date == subq.c.latest_date)
        )
        .filter(Bill.state == state.upper())
        .order_by(func.coalesce(BillHistory.date, Bill.last_updated).desc())
    )
    
    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    
    bills_out = [
        BillListItem(
            id=r[0].id,
            title=r[0].title,
            status=r[0].status,
            last_action_date=r[1],
            last_action=r[2]
        )
        for r in rows
    ]
    
    return PaginatedBills(
        total=total, limit=limit, offset=offset,
        next_offset=offset + limit if offset + limit < total else None,
        prev_offset=max(0, offset - limit),
        bills=bills_out
    )

@router.get("/{id}")
async def get_bill_detail(id: int, db: Session = Depends(get_db)):
    bill = db.query(Bill).filter(Bill.id == id).first()
    if not bill:
        raise HTTPException(404, "Bill not found")
    
    # Fetch FULL if missing/changed
    if not bill.raw_data:
        data = await legiscan.get_bill(id)
        bill_info = data['bill']
        if bill.change_hash != bill_info.get('change_hash', ''):
            bill.raw_data = bill_info  # Sponsors/history/texts!
            # TODO: Parse relations (Step 4)
            db.commit()
    
    raw = bill.raw_data or {}
    return {
        **bill.__dict__,
        "sponsors": raw.get('sponsors', []),
        "history": raw.get('history', []),
        "texts": raw.get('texts', []),
        "referrals": raw.get('referrals', [])
    }