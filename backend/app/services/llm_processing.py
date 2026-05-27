import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

TYPHOON_API_KEY = os.getenv("TYPHOON_API_KEY", "")
# SCB 10X Typhoon uses an OpenAI-compatible API
TYPHOON_BASE_URL = os.getenv("TYPHOON_BASE_URL", "https://api.opentyphoon.ai/v1")

client = OpenAI(api_key=TYPHOON_API_KEY, base_url=TYPHOON_BASE_URL) if TYPHOON_API_KEY else None

# Limit transcript length sent to LLM to avoid hitting context/token limits
# that cause unterminated JSON responses. ~8000 chars ≈ 2000 tokens.
MAX_TRANSCRIPT_CHARS = 8000

def extract_meeting_info(transcript: str):
    """
    Extracts summary, action items, and issues from the transcript using LLM.
    Truncates very long transcripts to avoid token limit errors.
    """
    if not client:
        return _mock_extraction(transcript)

    # Truncate to avoid exceeding model context window
    truncated = transcript[:MAX_TRANSCRIPT_CHARS]
    if len(transcript) > MAX_TRANSCRIPT_CHARS:
        truncated += "\n[...transcript truncated for length...]"
        logger.warning(f"Transcript truncated from {len(transcript)} to {MAX_TRANSCRIPT_CHARS} chars for LLM.")

    prompt = f"""You are an AI meeting assistant. Analyze the following meeting transcript and extract the requested information.
Respond with ONLY a valid JSON object with these keys:
- summary: A detailed summary of the meeting (string).
- topics: A list of important discussion topics (list of strings).
- decisions: A list of decisions and conclusions (list of strings).
- action_items: A list of objects, each with 'owner', 'task_description', and 'due_date' (ISO format string or null).
- issues: A list of objects, each with 'product', 'problem', and 'solution' (string or null).

Transcript:
{truncated}"""

    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=2048,
        )
        content = response.choices[0].message.content
        result = json.loads(content)
        return result
    except json.JSONDecodeError as e:
        logger.error(f"LLM returned invalid JSON: {e}. Raw content: {content[:500]}")
        return _mock_extraction(transcript)
    except Exception as e:
        logger.error(f"LLM Error during extraction: {e}")
        return _mock_extraction(transcript)

def qa_meeting(context: str, query: str):
    """
    Answers a question based on the meeting context.
    """
    if not client:
        return "I am a mock LLM. The API key is missing."

    prompt = f"""Answer the user's question based strictly on the provided context. If the answer is not in the context, say so.

Context:
{context}

Question: {query}"""

    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM Error during QA: {e}")
        return "Error calling LLM."

def _mock_extraction(transcript: str):
    return {
        "summary": "Mock summary — LLM call failed or API key not provided.",
        "topics": ["Mock Topic 1", "Mock Topic 2"],
        "decisions": ["Proceed with mock implementation"],
        "action_items": [
            {"owner": "Developer", "task_description": "Set TYPHOON_API_KEY in .env", "due_date": None}
        ],
        "issues": [
            {"product": "System", "problem": "LLM API Key missing or JSON parse error", "solution": "Check .env file and backend logs"}
        ]
    }

def evaluate_best_transcript(t1: str, t2: str, t3: str) -> str:
    """
    Evaluates 3 variations of a transcript and returns the most accurate, coherent,
    and consolidated version based on consensus.
    """
    if not client:
        # Fallback if no LLM: just return the first one
        return t1

    prompt = f"""You are an expert transcriber. You are given 3 variations of the same speech-to-text transcript generated with different sampling temperatures. 
Your goal is to output a single, final transcript that resolves any hallucinations, corrects grammar, and uses consensus among the 3 variations to produce the most accurate result.
Return ONLY the final corrected transcript text. Do not include explanations, formatting tags, or conversational filler.

Variation 1:
{t1}

Variation 2:
{t2}

Variation 3:
{t3}
"""

    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM Error during transcript evaluation: {e}")
        return t1
