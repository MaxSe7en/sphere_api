# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.db.session import get_db
# from app.services.legiscan_service import legiscan
# from app.models import bills, posts, users
# from app.schemas import schemas

# router = APIRouter()
# # service = legiscan_service.LegiScanService()

# @router.get("/{bill_id}", response_model=schemas.Bill)
# async def get_bill(bill_id: str, db: Session = Depends(get_db)):
#     print("================================================")
#     # return {"bill_id": bill_id}
#     # Check if bill exists in DB
#     db_bill = db.query(bills.Bill).filter(bills.Bill.id == bill_id).first()
    
#     if not db_bill:
#         # Fetch from LegiScan if not in DB
#         bill_data = await legiscan.get_bill(bill_id)
#         print(f"================================================{bill_data}")
#         if not bill_data:
#             raise HTTPException(status_code=404, detail="Bill not found")
        
#         # Save to DB
#         db_bill = bills.Bill(
#             id=bill_id,
#             state=bill_data["state"],
#             title=bill_data["title"],
#             status=bill_data["status"],
#             raw_data=bill_data
#         )
#         db.add(db_bill)
#         db.commit()
#         db.refresh(db_bill)
    
#     return db_bill


# routers/bills.py (Rewritten to handle full parsing, update detection with change_hash, and sub-models)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.legiscan_service import legiscan
from app.models import bills, posts, users
from app.models import Bill
from app.schemas import schemas
import datetime


router = APIRouter()

@router.get("/{bill_id}", response_model=schemas.Bill)
async def get_bill(bill_id: str, db: Session = Depends(get_db)):
    # Check if bill exists in DB
    db_bill = db.query(bills.Bill).filter(bills.Bill.id == bill_id).first()
    
    fetch_needed = True
    if db_bill:
        # Fetch from API to check for updates
        bill_data = await legiscan.get_bill(bill_id)
        print(f"================================================{bill_data}")
        if bill_data and bill_data.get('status') == 'OK':
            bill_info = bill_data['bill']
            if db_bill.change_hash == bill_info.get('change_hash'):
                fetch_needed = False  # No changes
            else:
                # Update DB with new data
                await update_bill_in_db(db, db_bill, bill_info)
        else:
            raise HTTPException(status_code=404, detail="Bill not found in API")

    if fetch_needed or not db_bill:
        bill_data = await legiscan.get_bill(bill_id)
        if not bill_data or bill_data.get('status') != 'OK':
            raise HTTPException(status_code=404, detail="Bill not found")
        
        bill_info = bill_data['bill']
        if not db_bill:
            db_bill = bills.Bill(id=bill_id)
        
        await update_bill_in_db(db, db_bill, bill_info)
    
    return db_bill

async def update_bill_in_db(db: Session, db_bill: bills.Bill, bill_info: dict):
    # Update core bill fields
    db_bill.bill_number = bill_info['bill_number']
    db_bill.change_hash = bill_info['change_hash']
    db_bill.title = bill_info['title']
    db_bill.description = bill_info['description']
    db_bill.status = bill_info['status']
    db_bill.status_date = datetime.datetime.strptime(bill_info['status_date'], '%Y-%m-%d') if bill_info['status_date'] else None
    db_bill.state = bill_info['state']
    db_bill.url = bill_info['url']
    db_bill.state_link = bill_info['state_link']
    db_bill.completed = bill_info['completed']
    db_bill.bill_type = bill_info['bill_type']
    db_bill.bill_type_id = bill_info['bill_type_id']
    db_bill.body = bill_info['body']
    db_bill.body_id = bill_info['body_id']
    db_bill.current_body = bill_info['current_body']
    db_bill.current_body_id = bill_info['current_body_id']
    db_bill.pending_committee_id = bill_info['pending_committee_id']
    db_bill.raw_data = bill_info

    # Set last_updated: Use max of status_date or latest history date
    last_updated = db_bill.status_date
    if bill_info['history']:
        last_history_date = max(datetime.datetime.strptime(h['date'], '%Y-%m-%d') for h in bill_info['history'] if h['date'])
        if last_history_date > last_updated:
            last_updated = last_history_date
    db_bill.last_updated = last_updated

    # Handle session
    session_info = bill_info['session']
    db_session = db.query(bills.Session).filter(bills.Session.id == session_info['session_id']).first()
    if not db_session:
        db_session = bills.Session(
            id=session_info['session_id'],
            state_id=session_info['state_id'],
            year_start=session_info['year_start'],
            year_end=session_info['year_end'],
            prefile=session_info['prefile'],
            sine_die=session_info['sine_die'],
            prior=session_info['prior'],
            special=session_info['special'],
            session_tag=session_info['session_tag'],
            session_title=session_info['session_title'],
            session_name=session_info['session_name']
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
    db_bill.session_id = db_session.id

    # Clear existing sub-records to avoid duplicates
    db.query(bills.Sponsor).filter(bills.Sponsor.bill_id == db_bill.id).delete()
    db.query(bills.Referral).filter(bills.Referral.bill_id == db_bill.id).delete()
    db.query(bills.BillHistory).filter(bills.BillHistory.bill_id == db_bill.id).delete()
    db.query(bills.BillText).filter(bills.BillText.bill_id == db_bill.id).delete()
    db.query(bills.CalendarEvent).filter(bills.CalendarEvent.bill_id == db_bill.id).delete()
    db.query(bills.Vote).filter(bills.Vote.bill_id == db_bill.id).delete()
    db.query(bills.Amendment).filter(bills.Amendment.bill_id == db_bill.id).delete()
    db.query(bills.Supplement).filter(bills.Supplement.bill_id == db_bill.id).delete()
    db.query(bills.Sast).filter(bills.Sast.bill_id == db_bill.id).delete()

    # Add sponsors
    for sponsor in bill_info['sponsors']:
        db_sponsor = bills.Sponsor(
            people_id=sponsor['people_id'],
            person_hash=sponsor['person_hash'],
            party_id=sponsor['party_id'],
            party=sponsor['party'],
            role_id=sponsor['role_id'],
            role=sponsor['role'],
            name=sponsor['name'],
            first_name=sponsor['first_name'],
            middle_name=sponsor['middle_name'],
            last_name=sponsor['last_name'],
            suffix=sponsor['suffix'],
            nickname=sponsor['nickname'],
            district=sponsor['district'],
            ftm_eid=sponsor['ftm_eid'],
            votesmart_id=sponsor['votesmart_id'],
            opensecrets_id=sponsor['opensecrets_id'],
            knowwho_pid=sponsor['knowwho_pid'],
            ballotpedia=sponsor['ballotpedia'],
            bioguide_id=sponsor['bioguide_id'],
            sponsor_type_id=sponsor['sponsor_type_id'],
            sponsor_order=sponsor['sponsor_order'],
            committee_sponsor=sponsor['committee_sponsor'],
            committee_id=sponsor['committee_id'],
            state_federal=sponsor['state_federal'],
            bill_id=db_bill.id
        )
        db.add(db_sponsor)

    # Add referrals
    for referral in bill_info['referrals']:
        db_referral = bills.Referral(
            date=datetime.datetime.strptime(referral['date'], '%Y-%m-%d') if referral['date'] else None,
            committee_id=referral['committee_id'],
            chamber=referral['chamber'],
            chamber_id=referral['chamber_id'],
            name=referral['name'],
            bill_id=db_bill.id
        )
        db.add(db_referral)

    # Add history
    for hist in bill_info['history']:
        db_hist = bills.BillHistory(
            date=datetime.datetime.strptime(hist['date'], '%Y-%m-%d') if hist['date'] else None,
            action=hist['action'],
            chamber=hist['chamber'],
            chamber_id=hist['chamber_id'],
            importance=hist['importance'],
            bill_id=db_bill.id
        )
        db.add(db_hist)

    # Add texts
    for text in bill_info['texts']:
        db_text = bills.BillText(
            doc_id=text['doc_id'],
            date=datetime.datetime.strptime(text['date'], '%Y-%m-%d') if text['date'] else None,
            type=text['type'],
            type_id=text['type_id'],
            mime=text['mime'],
            mime_id=text['mime_id'],
            url=text['url'],
            state_link=text['state_link'],
            text_size=text['text_size'],
            text_hash=text['text_hash'],
            bill_id=db_bill.id
        )
        db.add(db_text)

    # Add calendar events
    for cal in bill_info['calendar']:
        db_cal = bills.CalendarEvent(
            type_id=cal['type_id'],
            type=cal['type'],
            event_hash=cal.get('event_hash'),
            date=datetime.datetime.strptime(cal['date'], '%Y-%m-%d') if cal['date'] else None,
            time=cal['time'],
            location=cal['location'],
            description=cal['description'],
            bill_id=db_bill.id
        )
        db.add(db_cal)

    # Add sasts (similar bills)
    for sast in bill_info['sasts']:
        db_sast = bills.Sast(
            type_id=sast['type_id'],
            type=sast['type'],
            sast_bill_number=sast['sast_bill_number'],
            sast_bill_id=sast['sast_bill_id'],
            bill_id=db_bill.id
        )
        db.add(db_sast)

    # Add votes, amendments, supplements if present (expand as data becomes available)
    # For example:
    # for vote in bill_info['votes']:
    #     db_vote = bills.Vote(... )
    #     db.add(db_vote)

    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)

    # Trigger AI regeneration if text changed (using text_hash comparison)
    # For example, compare latest text_hash with previous; if changed, call LLM and update ai_* fields


@router.get("/states/{state}", response_model=list[schemas.Bill])
async def get_bills_for_state(state: str, db: Session = Depends(get_db)):
    # Optionally trigger sync if data is stale (e.g., check last sync time), but for now, return from DB
    # sync_state_bills.delay(state)  # Uncomment to sync on every request (not recommended for high traffic)
    
    db_bills = (db.query(bills.Bill)
                .filter(bills.Bill.state == state.upper())
                .options(
                    joinedload(bills.Bill.session),
                    joinedload(bills.Bill.sponsors),
                    joinedload(bills.Bill.referrals),
                    joinedload(bills.Bill.history),
                    joinedload(bills.Bill.texts),
                    joinedload(bills.Bill.calendar),
                    joinedload(bills.Bill.sasts)
                )
                .all())
    
    if not db_bills:
        raise HTTPException(status_code=404, detail=f"No bills found for state {state}. Try syncing first.")
    
    return db_bills

@router.get("/state_bills/{state}", response_model=list[schemas.BillOut])
def get_state_bills(
    state: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Bill).filter(Bill.state == state)
    total = query.count()
    bills = query.offset(offset).limit(limit).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "bills": bills
    }