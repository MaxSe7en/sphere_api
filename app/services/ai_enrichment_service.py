# app/services/ai_enrichment_service.py
from sqlalchemy.orm import Session
from app.models import bills
from app.services.ai_generator_service import generate_bill_ai_summary
import json


async def enrich_bill_with_ai(db: Session, bill_id: int, mode: str = "latest"):
    """
    Fetches bill text, runs AI analysis, and updates the Bill record
    with structured data (summary, impacts, pros/cons).
    """
    db_bill = db.query(bills.Bill).filter(bills.Bill.id == bill_id).first()
    print(f"Found bill: {db_bill.title if db_bill else 'None'}")
    
    if not db_bill:
        return {"error": "Bill not found"}

    # Generate AI insights
    ai_result = await generate_bill_ai_summary(db, bill_id, mode)

    if ai_result.get("error"):
        return ai_result

    # Update bill record with structured data
    db_bill.ai_summary = ai_result.get("ai_summary", "")
    
    # Store impacts as JSON (assuming column type supports JSON/JSONB)
    db_bill.ai_impacts = json.dumps(ai_result.get("ai_impacts", []))
    
    # Store pros/cons as JSON
    db_bill.ai_pro_con = json.dumps(ai_result.get("ai_pro_con", []))

    db.commit()
    db.refresh(db_bill)
    
    return {
        "success": True,
        "bill_id": bill_id,
        "ai_summary": db_bill.ai_summary,
        "ai_impacts": ai_result.get("ai_impacts", []),
        "ai_pro_con": ai_result.get("ai_pro_con", [])
    }