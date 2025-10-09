# app/services/ai_generator_service.py
import io
import json
import requests
from typing import Optional, Literal, Dict, List
from openai import OpenAI
from PyPDF2 import PdfReader

from app.models import BillText
from app.db.session import get_db
from app.core.config import settings

client = OpenAI(
    api_key=settings.OPENAI_ORGANIZATION,
    base_url="https://openrouter.ai/api/v1",
)

def extract_pdf_text(url: str) -> Optional[str]:
    """
    Download and extract text from a PDF at the given URL.
    Returns None if download or extraction fails.
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        with io.BytesIO(response.content) as pdf_file:
            reader = PdfReader(pdf_file)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text.strip()
    except Exception as e:
        print(f"⚠️ Failed to extract PDF from {url}: {e}")
        return None


async def generate_bill_ai_summary(
    db,
    bill_id: int,
    mode: Literal["latest", "full"] = "latest"
) -> Dict:
    """
    Generates structured AI analysis for a bill including:
    - Summary (string)
    - Impacts (list of categorized impacts)
    - Pros and cons (list of arguments)
    
    mode:
        - 'latest' → use the most recent bill text
        - 'full' → combine all bill versions
    """
    # Step 1: Fetch bill texts from DB
    if mode == "latest":
        texts = (
            db.query(BillText)
            .filter(BillText.bill_id == bill_id)
            .order_by(BillText.date.desc())
            .limit(1)
            .all()
        )
    else:
        texts = (
            db.query(BillText)
            .filter(BillText.bill_id == bill_id)
            .order_by(BillText.date.asc())
            .all()
        )

    if not texts:
        return {"error": "No bill texts found for this bill."}

    # Step 2: Extract text from PDFs
    print(f"Extracting text from {len(texts)} bill version(s)...")
    combined_texts = []
    for t in texts:
        print(f"Processing bill text ID {t.id} from {t.state_link}")
        if not t.state_link or not t.state_link.endswith("=pdf"):
            continue
        pdf_text = extract_pdf_text(t.state_link)
        print(f"Extracted {len(pdf_text) if pdf_text else 0} chars from {t.state_link}")
        if pdf_text:
            combined_texts.append(
                f"=== Version {t.mime or 'unknown'} ===\n{pdf_text[:8000]}"
            )

    if not combined_texts:
        return {"error": "Failed to extract any text from bill PDFs."}

    full_context = "\n\n".join(combined_texts)

    # Step 3: Generate structured AI analysis
    try:
        prompt = f"""
You are an expert legislative analyst. Analyze the following bill text and provide a structured JSON response.

BILL TEXT:
{full_context[:24000]}

You must respond with ONLY valid JSON in exactly this format (no additional text):
{{
  "summary": "A concise 2-3 sentence summary of the bill's main purpose and key provisions",
  "impacts": [
    {{"category": "Category Name", "description": "Specific impact description"}},
    {{"category": "Another Category", "description": "Another impact description"}}
  ],
  "pros_cons": [
    {{"type": "pro", "argument": "Specific positive argument"}},
    {{"type": "pro", "argument": "Another positive argument"}},
    {{"type": "con", "argument": "Specific criticism or concern"}},
    {{"type": "con", "argument": "Another criticism or concern"}}
  ]
}}

Guidelines:
- Summary: 150-250 words, focus on main objectives and funding/requirements
- Impacts: 3-5 key impacts, use categories like "Education", "Healthcare", "Economy", "Environment", "Public Safety", "Rural Communities", etc.
- Pros/Cons: 2-4 of each, be specific and balanced

Respond with ONLY the JSON object, no other text.
"""

        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert legislative analyst. Always respond with valid JSON only."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        ai_output = response.choices[0].message.content.strip()
        
        # Try to extract JSON if wrapped in markdown code blocks
        if ai_output.startswith("```"):
            # Remove markdown code block markers
            ai_output = ai_output.split("```")[1]
            if ai_output.startswith("json"):
                ai_output = ai_output[4:]
            ai_output = ai_output.strip()

        # Parse JSON response
        try:
            parsed_data = json.loads(ai_output)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw AI output: {ai_output}")
            return {
                "error": "Failed to parse AI response",
                "raw_output": ai_output
            }

        # Step 4: Format response for database storage
        return {
            "bill_id": bill_id,
            "ai_summary": parsed_data.get("summary", ""),
            "ai_impacts": parsed_data.get("impacts", []),
            "ai_pro_con": parsed_data.get("pros_cons", []),
            "mode_used": mode,
            "success": True
        }

    except Exception as e:
        print(f"AI generation error: {e}")
        return {"error": str(e), "success": False}
