async def update_bill_in_db(db: Session, db_bill: bills.Bill, bill_info: dict):
    """
    Updates a Bill record and all its related data (sponsors, referrals, history, etc.)
    If the bill or its text changed, regenerate AI summary, impacts, and pros/cons.
    """

    # === Core fields ===
    db_bill.bill_number = bill_info.get('bill_number')
    db_bill.change_hash = bill_info.get('change_hash')
    db_bill.title = bill_info.get('title')
    db_bill.description = bill_info.get('description')
    db_bill.status = bill_info.get('status')
    db_bill.status_date = (
        datetime.datetime.strptime(bill_info['status_date'], '%Y-%m-%d')
        if bill_info.get('status_date') else None
    )
    db_bill.state = bill_info.get('state')
    db_bill.url = bill_info.get('url')
    db_bill.state_link = bill_info.get('state_link')
    db_bill.completed = bill_info.get('completed')
    db_bill.bill_type = bill_info.get('bill_type')
    db_bill.bill_type_id = bill_info.get('bill_type_id')
    db_bill.body = bill_info.get('body')
    db_bill.body_id = bill_info.get('body_id')
    db_bill.current_body = bill_info.get('current_body')
    db_bill.current_body_id = bill_info.get('current_body_id')
    db_bill.pending_committee_id = bill_info.get('pending_committee_id')
    db_bill.raw_data = bill_info

    # === Compute last_updated (based on history or status date) ===
    last_updated = db_bill.status_date
    if bill_info.get('history'):
        last_history_date = max(
            datetime.datetime.strptime(h['date'], '%Y-%m-%d')
            for h in bill_info['history'] if h.get('date')
        )
        if not last_updated or last_history_date > last_updated:
            last_updated = last_history_date
    db_bill.last_updated = last_updated

    # === Handle session info ===
    session_info = bill_info.get('session')
    if session_info:
        db_session = db.query(bills.Session).filter(
            bills.Session.id == session_info['session_id']
        ).first()
        if not db_session:
            db_session = bills.Session(
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
        db_bill.session_id = db_session.id

    # === Clear old related data ===
    db.query(bills.Sponsor).filter(bills.Sponsor.bill_id == db_bill.id).delete()
    db.query(bills.Referral).filter(bills.Referral.bill_id == db_bill.id).delete()
    db.query(bills.BillHistory).filter(bills.BillHistory.bill_id == db_bill.id).delete()
    db.query(bills.BillText).filter(bills.BillText.bill_id == db_bill.id).delete()
    db.query(bills.CalendarEvent).filter(bills.CalendarEvent.bill_id == db_bill.id).delete()
    db.query(bills.Vote).filter(bills.Vote.bill_id == db_bill.id).delete()
    db.query(bills.Amendment).filter(bills.Amendment.bill_id == db_bill.id).delete()
    db.query(bills.Supplement).filter(bills.Supplement.bill_id == db_bill.id).delete()
    db.query(bills.Sast).filter(bills.Sast.bill_id == db_bill.id).delete()

    # === Add sub-records ===
    for sponsor in bill_info.get('sponsors', []):
        db.add(bills.Sponsor(bill_id=db_bill.id, **sponsor))

    for referral in bill_info.get('referrals', []):
        db.add(bills.Referral(
            bill_id=db_bill.id,
            date=datetime.datetime.strptime(referral['date'], '%Y-%m-%d')
            if referral.get('date') else None,
            **{k: v for k, v in referral.items() if k not in ['bill_id', 'date']}
        ))

    for hist in bill_info.get('history', []):
        db.add(bills.BillHistory(
            bill_id=db_bill.id,
            date=datetime.datetime.strptime(hist['date'], '%Y-%m-%d')
            if hist.get('date') else None,
            **{k: v for k, v in hist.items() if k not in ['bill_id', 'date']}
        ))

    for text in bill_info.get('texts', []):
        db.add(bills.BillText(
            bill_id=db_bill.id,
            date=datetime.datetime.strptime(text['date'], '%Y-%m-%d')
            if text.get('date') else None,
            **{k: v for k, v in text.items() if k not in ['bill_id', 'date']}
        ))

    for cal in bill_info.get('calendar', []):
        db.add(bills.CalendarEvent(
            bill_id=db_bill.id,
            date=datetime.datetime.strptime(cal['date'], '%Y-%m-%d')
            if cal.get('date') else None,
            **{k: v for k, v in cal.items() if k not in ['bill_id', 'date']}
        ))

    for sast in bill_info.get('sasts', []):
        db.add(bills.Sast(bill_id=db_bill.id, **sast))

    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)

    # === AI Enrichment (summary, impacts, pros/cons) ===
    latest_text = bill_info['texts'][-1]['url'] if bill_info.get('texts') else None

    should_generate_ai = (
        not db_bill.ai_summary or
        latest_text != getattr(db_bill, "latest_text_url", None)
    )

    if should_generate_ai:
        print(f"🤖 Generating AI summary for Bill {db_bill.id}...")
        ai_result = await generate_ai_summary(
            title=db_bill.title or "",
            description=db_bill.description or "",
            text_content=None  # optional: fetch text from URL later
        )

        db_bill.ai_summary = ai_result.get("summary")
        db_bill.ai_impacts = ai_result.get("impacts")
        db_bill.ai_pro_con = ai_result.get("pros_cons")
        db_bill.latest_text_url = latest_text

        db.commit()
        db.refresh(db_bill)

    print(f"✅ Bill {db_bill.id} updated successfully.")
    return db_bill

