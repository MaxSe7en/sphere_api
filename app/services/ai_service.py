from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def generate_ai_summary(title: str, description: str, text_content: str | None = None):
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

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4o" for better quality
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
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
