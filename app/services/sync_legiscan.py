# app/services/sync_legiscan.py
import asyncio
from datetime import datetime
from app.db.session import SessionLocal
from app.models import Bill, Session as BillSession
from app.core.config import settings
from app.services.legiscan_service import legiscan




async def sync_state_bills(state: str):
    """Fetch and update all bills for a given state."""
    db = SessionLocal()

    try:
        data = await legiscan.get_bills_for_state(state)
        if data.get("status") != "OK":
            return {"error": data}

        if data.get("status") != "OK":
            return {"error": f"Failed to fetch data: {data}"}

        masterlist = data["masterlist"]

        # --- handle session ---
        session_info = masterlist.pop("session", None)
        if session_info:
            db_session = (
                db.query(BillSession)
                .filter(BillSession.id == session_info["session_id"])
                .first()
            )
            if not db_session:
                db_session = BillSession(
                    id=session_info["session_id"],
                    state_id=session_info["state_id"],
                    year_start=session_info["year_start"],
                    year_end=session_info["year_end"],
                    prefile=session_info.get("prefile", 0),
                    sine_die=session_info.get("sine_die", 0),
                    prior=session_info.get("prior", 0),
                    special=session_info.get("special", 0),
                    session_tag=session_info["session_tag"],
                    session_title=session_info["session_title"],
                    session_name=session_info["session_name"],
                )
                db.add(db_session)
                db.commit()
            session_id = db_session.id
        else:
            session_id = None

        updated, skipped = [], []

        # --- loop over bills ---
        for key, item in masterlist.items():
            if not isinstance(item, dict) or "bill_id" not in item:
                continue

            bill_id = item["bill_id"]
            db_bill = db.query(Bill).filter(Bill.id == bill_id).first()

            # Skip if change_hash is unchanged
            if db_bill and db_bill.change_hash == item["change_hash"]:
                skipped.append(bill_id)
                continue

            if not db_bill:
                db_bill = Bill(id=bill_id, state=state, session_id=session_id)
                db.add(db_bill)

            db_bill.bill_number = item["number"]
            db_bill.change_hash = item["change_hash"]
            db_bill.title = item["title"]
            db_bill.description = item["description"]
            db_bill.url = item["url"]
            db_bill.status = item["status"]
            db_bill.status_date = (
                datetime.strptime(item["status_date"], "%Y-%m-%d")
                if item["status_date"]
                else None
            )
            db_bill.last_action = item.get("last_action")
            db_bill.last_action_date = (
                datetime.strptime(item["last_action_date"], "%Y-%m-%d")
                if item.get("last_action_date")
                else None
            )
            db_bill.last_synced = datetime.now(timezone.utc)

            db.commit()
            updated.append(bill_id)

        return {"updated": updated, "skipped": skipped}
    finally:
        db.close()


if __name__ == "__main__":
    # Manual run: sync MN bills
    result = asyncio.run(sync_state_bills("MN"))
    print(result)
