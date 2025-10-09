# app/api/v1/endpoints/ai.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Bill
from app.services.ai_service import generate_openai_summary
from app.services.ai_generator_service import generate_bill_ai_summary
from app.services.ai_enrichment_service import enrich_bill_with_ai

router = APIRouter()

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


@router.post("/bills/{bill_id}/enrich")
async def enrich_bill_ai(bill_id: int, db: Session = Depends(get_db)):
    updated_bill = await enrich_bill_with_ai(db, bill_id)
    if not updated_bill:
        raise HTTPException(status_code=404, detail="No bill text found or bill missing")
    return updated_bill


@router.get("/{bill_id}/ai")
async def generate_bill_ai_data(
    bill_id: int, 
    mode: str = "latest", 
    db: Session = Depends(get_db)
):
    """
    Generate and return AI analysis for a bill.
    Returns structured data with summary, impacts, and pros/cons.
    """
    result = await enrich_bill_with_ai(db, bill_id, mode)
    
    if result.get("error"):
        return {"error": result["error"]}, 400
    
    # Parse JSON strings back to objects for API response
    return {
        "bill_id": result["bill_id"],
        "ai_summary": result["ai_summary"],
        "ai_impacts": json.loads(result["ai_impacts"]) if isinstance(result["ai_impacts"], str) else result["ai_impacts"],
        "ai_pro_con": json.loads(result["ai_pro_con"]) if isinstance(result["ai_pro_con"], str) else result["ai_pro_con"],
        "success": True
    }


@router.post("/{bill_id}/ai/regenerate")
async def regenerate_bill_ai_data(
    bill_id: int,
    mode: str = "latest",
    db: Session = Depends(get_db)
):
    """
    Force regeneration of AI analysis for a bill.
    Useful for updating existing analyses.
    """
    result = await enrich_bill_with_ai(db, bill_id, mode)
    return result