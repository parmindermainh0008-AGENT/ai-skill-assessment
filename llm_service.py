"""
LLM Service — uses Groq's LLaMA model to:
  1. Generate questions based on domain + level
  2. Evaluate the user's answers and give a score + feedback

Both functions require strict JSON output so it can be used directly in the UI.
"""

import json
import re
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, NUM_QUESTIONS

client = Groq(api_key=GROQ_API_KEY)


def _extract_json(text: str):
    """The LLM sometimes adds extra text before/after the JSON — this cleans it up."""
    text = text.strip()
    text = re.sub(r"^```json\s*|^```\s*|```$", "", text, flags=re.MULTILINE).strip()
    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def generate_questions(domain: str, level: str, num_questions: int = NUM_QUESTIONS):
    """
    Generates questions based on the domain and difficulty level.
    Each question's type can be "conceptual" or "scenario-based".

    Returns: list of dicts -> [{"id": 1, "question": "...", "type": "conceptual"}, ...]
    """
    system_prompt = f"""You are an expert technical interviewer and educator specializing in {domain}.
Generate exactly {num_questions} interview-style questions for a {level} level candidate in the domain "{domain}".

Rules:
- Mix conceptual and applied/scenario-based questions.
- Questions should genuinely test understanding, not just definitions.
- Difficulty must match the "{level}" level precisely.
- Return ONLY a valid JSON array, no preamble, no markdown, no explanation.

Format:
[
  {{"id": 1, "question": "...", "type": "conceptual"}},
  {{"id": 2, "question": "...", "type": "scenario"}}
]
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate the {num_questions} questions now."},
        ],
        temperature=0.7,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content
    try:
        questions = _extract_json(raw)
        return questions
    except (json.JSONDecodeError, AttributeError):
        # Fallback in case JSON parsing fails
        return [{"id": 1, "question": raw, "type": "conceptual"}]


def evaluate_answers(domain: str, level: str, qa_pairs: list):
    """
    qa_pairs: list of {"question": "...", "answer": "..."}

    Returns: {
        "evaluations": [
            {"question": "...", "score": 8, "max_score": 10, "feedback": "...", "correct_points": "...", "missing_points": "..."}
        ],
        "total_score": 34,
        "max_score": 50,
        "overall_feedback": "..."
    }
    """
    system_prompt = f"""You are a strict but fair technical evaluator for {domain} at {level} level.
For each question-answer pair below, evaluate the user's answer.

Scoring rules:
- Each answer is scored out of 10.
- Give credit for correct concepts even if wording is different from textbook definitions.
- Penalize factually incorrect statements clearly.
- If the answer is empty or "I don't know", score it 0 with encouraging feedback.
- Provide brief, specific, constructive feedback in clear, simple English (max 2-3 sentences). Do NOT use Hindi, Hinglish, or any other language — English only, regardless of what language the answer was written in.

Return ONLY a valid JSON object in this exact format, no markdown, no preamble:
{{
  "evaluations": [
    {{"question": "...", "score": 8, "max_score": 10, "feedback": "...", "missing_points": "..."}}
  ],
  "overall_feedback": "2-3 line summary of overall performance and what to improve, in English only"
}}
"""

    user_content = "Here are the question-answer pairs to evaluate:\n\n"
    for i, pair in enumerate(qa_pairs, 1):
        user_content += f"Q{i}: {pair['question']}\nAnswer: {pair['answer'] or '(no answer given)'}\n\n"

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content
    result = _extract_json(raw)

    total_score = sum(e.get("score", 0) for e in result["evaluations"])
    max_score = sum(e.get("max_score", 10) for e in result["evaluations"])
    result["total_score"] = total_score
    result["max_score"] = max_score

    return result