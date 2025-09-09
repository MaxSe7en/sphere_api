# celery_tasks.py (New file for Celery tasks; assume Celery is set up as per earlier architecture)

from celery import Celery
# import requests
from datetime import datetime
from app.db.session import SessionLocal  # Assume you have a session maker
from app.models.bills import Bill, Session as BillSession
# from app.routers.bills import update_bill_in_db  # Import the update function; make it sync if needed
from app.api.v1.endpoints.bills import update_bill_in_db
from app.core.config import settings
from app.services.legiscan_service import legiscan

# celery = Celery("tasks", broker="redis://localhost:6379/0")  # As per earlier

base_url = "https://api.legiscan.com"
api_key = settings.LEGISCAN_API_KEY

# @celery.task
async def sync_state_bills(state: str):
    db = SessionLocal()
    try:
        response = await legiscan.get_bills_for_state(state) #requests.get(f"{base_url}/?key={api_key}&op=getMasterList&state={state}")
        master_data = response#.json()
        
        # if master_data.get('status') != 'OK':
        #     return {"error": "Failed to fetch master list"}
        
        masterlist = master_data['masterlist']
        
        # Handle session
        session_info = masterlist.pop('session', None)
        if session_info:
            db_session = db.query(BillSession).filter(BillSession.id == session_info['session_id']).first()
            if not db_session:
                db_session = BillSession(
                    id=session_info['session_id'],
                    state_id=session_info['state_id'],
                    year_start=session_info['year_start'],
                    year_end=session_info['year_end'],
                    prefile=session_info.get('prefile', 0),
                    sine_die=session_info.get('sine_die', 0),
                    prior=session_info.get('prior', 0),
                    special=session_info.get('special', 0),
                    session_tag=session_info['session_tag'],
                    session_title=session_info['session_title'],
                    session_name=session_info['session_name']
                )
                db.add(db_session)
                db.commit()
                db.refresh(db_session)
            session_id = db_session.id
        else:
            session_id = None
        
        updated_bills = []
        for key, item in masterlist.items():
            if isinstance(item, dict) and 'bill_id' in item:
                bill_id = item['bill_id']
                db_bill = db.query(Bill).filter(Bill.id == bill_id).first()
                
                update_needed = True
                if db_bill and db_bill.change_hash == item['change_hash']:
                    update_needed = False
                
                # Update summary fields regardless if new or changed
                if not db_bill:
                    db_bill = Bill(id=bill_id, state=state, session_id=session_id)
                    db.add(db_bill)
                
                db_bill.bill_number = item['number']
                db_bill.change_hash = item['change_hash']
                db_bill.title = item['title']
                db_bill.description = item['description']
                db_bill.url = item['url']
                db_bill.status = item['status']
                db_bill.status_date = datetime.strptime(item['status_date'], '%Y-%m-%d') if item['status_date'] else None
                db_bill.last_updated = datetime.strptime(item['last_action_date'], '%Y-%m-%d') if item['last_action_date'] else None
                
                db.commit()
                db.refresh(db_bill)
                
                if update_needed:
                    # Fetch full details
                    bill_response = requests.get(f"{base_url}/?key={api_key}&op=getBill&id={bill_id}")
                    bill_data = bill_response.json()
                    if bill_data.get('status') == 'OK':
                        update_bill_in_db(db, db_bill, bill_data['bill'])  # Assuming update_bill_in_db is sync; adjust if async
                
                updated_bills.append(bill_id)
        
        return {"updated_bills": updated_bills}
    finally:
        db.close()

# Example usage:
result = sync_state_bills("MN")