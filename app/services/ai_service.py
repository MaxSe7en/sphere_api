# app/services/ai_service.py
from openai import OpenAI
from app.core.config import settings

# client = OpenAI(api_key=settings.OPENAI_ORGANIZATION)
client = OpenAI(
    api_key=settings.OPENAI_ORGANIZATION,
    base_url="https://openrouter.ai/api/v1",  # 👈 OpenRouter base
)

async def generate_bill_summary(bill_text: str) -> dict:
    """
    Uses OpenAI to analyze a legislative bill text and return:
      - ai_summary: short paragraph summary
      - ai_impacts: list of key impacts (dict form)
      - ai_pro_con: list of pros and cons (dict form)
    """

    prompt = f"""
    You are a legislative policy analyst. Analyze the bill text below and produce JSON output in this exact structure:

    {{
      "summary": "string (3-5 sentences summary of what the bill does)",
      "impacts": [
        {{"category": "Economy", "description": "Expected economic effect"}},
        {{"category": "Public", "description": "Expected public or social impact"}}
      ],
      "pros_cons": [
        {{"type": "pro", "description": "Positive impact or argument"}},
        {{"type": "con", "description": "Negative impact or concern"}}
      ]
    }}

    Bill Text:
    {bill_text[:8000]}
    """

    # response = client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     response_format={"type": "json_object"},
    #     messages=[
    #         {"role": "system", "content": "You are an expert legislative policy analyst."},
    #         {"role": "user", "content": prompt},
    #     ],
    #     temperature=0.4,
    # )

    response = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct",
        messages=[
            {"role": "system", "content": "You are an expert legislative policy analyst."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        extra_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "Sphere Legislative Analyzer"
        }
    )
    # Parse JSON directly from OpenAI structured output
    ai_data = response.choices[0].message.parsed

    return {
        "ai_summary": ai_data.get("summary"),
        "ai_impacts": ai_data.get("impacts", []),
        "ai_pro_con": ai_data.get("pros_cons", []),
    }


async def generate_openai_summary(title: str, description: str, text_content: str | None = None):
    """
    Generates a structured AI summary, impacts, and pros/cons for a bill.
    """
    prompt = f"""
    You are a legislative analysis assistant.
    Given the following bill information:

    Title: {title}
    Description: {description}
    Text: {text_content or '[No full text provided]'}

    Provide:
    1. A concise summary (max 5 sentences)
    2. The potential social, economic, or environmental impacts
    3. The main pros and cons in bullet form
    """

    # response = client.chat.completions.create(
    #     model="gpt-4o-mini",  # or "gpt-4o" for better quality
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.7,
    # )
    response = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        extra_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "Sphere Legislative Analyzer"
        }
    )

    content = response.choices[0].message.content
    return parse_ai_response(content)


def parse_ai_response(text: str):
    """
    Parses AI output into structured dict for storage.
    """
    parts = text.split("\n\n")
    return {
        "summary": parts[0].strip() if len(parts) > 0 else None,
        "impacts": parts[1].strip() if len(parts) > 1 else None,
        "pros_cons": parts[2].strip() if len(parts) > 2 else None,
    }
