import datetime
from sqlalchemy.orm import Session
from app.models import bills
from app.services.legiscan_service import LegiScanService
from app.services.ai_service import generate_bill_summary

legiscan = LegiScanService()

async def sync_bill_from_legiscan(db: Session, bill_id: str):
    """
    Fetches a bill from LegiScan, updates DB if changed, and triggers AI summary generation.
    """
    # Check existing bill
    db_bill = db.query(bills.Bill).filter(bills.Bill.id == bill_id).first()

    # Fetch from LegiScan API
    bill_data = await legiscan.get_bill(bill_id)
    if not bill_data or bill_data.get("status") != "OK":
        return None

    bill_info = bill_data["bill"]

    # Skip update if change_hash is same
    if db_bill and db_bill.change_hash == bill_info.get("change_hash"):
        return db_bill  # up-to-date

    # Create or update Bill model
    if not db_bill:
        db_bill = bills.Bill(id=bill_id)

    db_bill.bill_number = bill_info["bill_number"]
    db_bill.change_hash = bill_info["change_hash"]
    db_bill.title = bill_info["title"]
    db_bill.description = bill_info["description"]
    db_bill.status = bill_info["status"]
    db_bill.status_date = (
        datetime.datetime.strptime(bill_info["status_date"], "%Y-%m-%d")
        if bill_info.get("status_date")
        else None
    )
    db_bill.state = bill_info["state"]
    db_bill.url = bill_info["url"]
    db_bill.state_link = bill_info["state_link"]
    db_bill.completed = bill_info["completed"]
    db_bill.bill_type = bill_info["bill_type"]
    db_bill.bill_type_id = bill_info["bill_type_id"]
    db_bill.body = bill_info["body"]
    db_bill.body_id = bill_info["body_id"]
    db_bill.current_body = bill_info["current_body"]
    db_bill.current_body_id = bill_info["current_body_id"]
    db_bill.pending_committee_id = bill_info["pending_committee_id"]
    db_bill.raw_data = bill_info

    # Calculate last updated date
    last_updated = db_bill.status_date
    if bill_info.get("history"):
        last_history_date = max(
            datetime.datetime.strptime(h["date"], "%Y-%m-%d")
            for h in bill_info["history"]
            if h.get("date")
        )
        if not last_updated or last_history_date > last_updated:
            last_updated = last_history_date
    db_bill.last_updated = last_updated

    # Handle session info
    session_info = bill_info["session"]
    db_session = db.query(bills.Session).filter(
        bills.Session.id == session_info["session_id"]
    ).first()

    if not db_session:
        db_session = bills.Session(
            id=session_info["session_id"],
            state_id=session_info["state_id"],
            year_start=session_info["year_start"],
            year_end=session_info["year_end"],
            prefile=session_info["prefile"],
            sine_die=session_info["sine_die"],
            prior=session_info["prior"],
            special=session_info["special"],
            session_tag=session_info["session_tag"],
            session_title=session_info["session_title"],
            session_name=session_info["session_name"],
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

    db_bill.session_id = db_session.id

    # Clear related child records to avoid duplicates
    db.query(bills.Sponsor).filter(bills.Sponsor.bill_id == db_bill.id).delete()
    db.query(bills.Referral).filter(bills.Referral.bill_id == db_bill.id).delete()
    db.query(bills.BillHistory).filter(bills.BillHistory.bill_id == db_bill.id).delete()
    db.query(bills.BillText).filter(bills.BillText.bill_id == db_bill.id).delete()
    db.query(bills.CalendarEvent).filter(bills.CalendarEvent.bill_id == db_bill.id).delete()
    db.query(bills.Sast).filter(bills.Sast.bill_id == db_bill.id).delete()

    # Insert sponsors
    for sponsor in bill_info.get("sponsors", []):
        db_sponsor = bills.Sponsor(
            people_id=sponsor["people_id"],
            person_hash=sponsor["person_hash"],
            party_id=sponsor["party_id"],
            party=sponsor["party"],
            role_id=sponsor["role_id"],
            role=sponsor["role"],
            name=sponsor["name"],
            first_name=sponsor["first_name"],
            middle_name=sponsor["middle_name"],
            last_name=sponsor["last_name"],
            suffix=sponsor["suffix"],
            nickname=sponsor["nickname"],
            district=sponsor["district"],
            ftm_eid=sponsor["ftm_eid"],
            votesmart_id=sponsor["votesmart_id"],
            opensecrets_id=sponsor["opensecrets_id"],
            knowwho_pid=sponsor["knowwho_pid"],
            ballotpedia=sponsor["ballotpedia"],
            bioguide_id=sponsor["bioguide_id"],
            sponsor_type_id=sponsor["sponsor_type_id"],
            sponsor_order=sponsor["sponsor_order"],
            committee_sponsor=sponsor["committee_sponsor"],
            committee_id=sponsor["committee_id"],
            state_federal=sponsor["state_federal"],
            bill_id=db_bill.id,
        )
        db.add(db_sponsor)

    # Insert referrals
    for referral in bill_info.get("referrals", []):
        db_ref = bills.Referral(
            date=datetime.datetime.strptime(referral["date"], "%Y-%m-%d")
            if referral.get("date")
            else None,
            committee_id=referral["committee_id"],
            chamber=referral["chamber"],
            chamber_id=referral["chamber_id"],
            name=referral["name"],
            bill_id=db_bill.id,
        )
        db.add(db_ref)

    # Insert history
    for hist in bill_info.get("history", []):
        db_hist = bills.BillHistory(
            date=datetime.datetime.strptime(hist["date"], "%Y-%m-%d")
            if hist.get("date")
            else None,
            action=hist["action"],
            chamber=hist["chamber"],
            chamber_id=hist["chamber_id"],
            importance=hist["importance"],
            bill_id=db_bill.id,
        )
        db.add(db_hist)

    # Insert texts
    for text in bill_info.get("texts", []):
        db_text = bills.BillText(
            doc_id=text["doc_id"],
            date=datetime.datetime.strptime(text["date"], "%Y-%m-%d")
            if text.get("date")
            else None,
            type=text["type"],
            type_id=text["type_id"],
            mime=text["mime"],
            mime_id=text["mime_id"],
            url=text["url"],
            state_link=text["state_link"],
            text_size=text["text_size"],
            text_hash=text["text_hash"],
            bill_id=db_bill.id,
        )
        db.add(db_text)

    # Calendar
    for cal in bill_info.get("calendar", []):
        db_cal = bills.CalendarEvent(
            type_id=cal["type_id"],
            type=cal["type"],
            event_hash=cal.get("event_hash"),
            date=datetime.datetime.strptime(cal["date"], "%Y-%m-%d")
            if cal.get("date")
            else None,
            time=cal.get("time"),
            location=cal.get("location"),
            description=cal.get("description"),
            bill_id=db_bill.id,
        )
        db.add(db_cal)

    # Similar bills (SASTs)
    for sast in bill_info.get("sasts", []):
        db_sast = bills.Sast(
            type_id=sast["type_id"],
            type=sast["type"],
            sast_bill_number=sast["sast_bill_number"],
            sast_bill_id=sast["sast_bill_id"],
            bill_id=db_bill.id,
        )
        db.add(db_sast)

    # ✅ Generate AI summary (latest bill text)
    if bill_info.get("texts"):
        latest_text = max(bill_info["texts"], key=lambda t: t["date"])
        bill_text = latest_text.get("text", "")
        if bill_text:
            ai_result = await generate_bill_summary(bill_text)
            db_bill.ai_summary = ai_result["summary"]
            db_bill.ai_impacts = ai_result["impacts"]
            db_bill.ai_pro_con = ai_result["pros_cons"]

    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)

    return db_bill
