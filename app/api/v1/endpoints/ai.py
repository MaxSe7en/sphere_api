from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Bill
from app.services.ai_service import generate_ai_summary

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/generate/{bill_id}")
async def regenerate_ai_for_bill(bill_id: int, db: Session = Depends(get_db)):
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    ai_result = await generate_ai_summary(bill.title, bill.description)
    bill.ai_summary = ai_result["summary"]
    bill.ai_impacts = ai_result["impacts"]
    bill.ai_pro_con = ai_result["pros_cons"]
    db.commit()
    return {"bill_id": bill_id, "status": "AI analysis updated", "ai": ai_result}
