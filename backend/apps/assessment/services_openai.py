from django.conf import settings
from rest_framework.exceptions import ValidationError

from openai import OpenAI


def _get_client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        raise ValidationError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=settings.OPENAI_API_KEY)

# JSON Schema the model MUST follow (Structured Outputs)
MCQ_SCHEMA = {
    "name": "mcq_set",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "items": {
                "type": "array",
                "minItems": 1,
                "maxItems": 30,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "question": {"type": "string"},
                        "options": {
                            "type": "array",
                            "minItems": 4,
                            "maxItems": 4,
                            "items": {"type": "string"},
                        },
                        "correct_index": {"type": "integer", "minimum": 0, "maximum": 3},
                        "explanation": {"type": "string"},
                    },
                    "required": ["question", "options", "correct_index", "explanation"],
                },
            }
        },
        "required": ["items"],
    },
}

def generate_mcqs(*, topic: str, count: int, difficulty: str, grade_level: str, language: str) -> dict:
    lang_name = "Nepali" if language == "ne" else "English"

    prompt = f"""
Generate {count} multiple choice questions about: {topic}.
Difficulty: {difficulty}
Grade level (optional): {grade_level or "general"}

Rules:
- Output ONLY valid JSON matching the schema.
- Exactly 4 options per question.
- correct_index must point to the correct option.
- Provide a short explanation.
- Language: {lang_name}
"""

    # Responses API is recommended for new projects. :contentReference[oaicite:1]{index=1}
    resp = _get_client().responses.create(
        model="gpt-5-nano",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "json_schema": MCQ_SCHEMA,
                "strict": True,
            }
        },
    )

    # With Structured Outputs, the response will conform to your schema. :contentReference[oaicite:2]{index=2}
    return resp.output_parsed  # parsed JSON object
