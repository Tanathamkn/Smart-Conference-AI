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

    prompt = f"""คุณคือผู้ช่วย AI สำหรับวิเคราะห์การประชุม มีความเชี่ยวชาญในการสกัดข้อมูลสำคัญจากบทถอดความการประชุมภาษาไทยและภาษาอังกฤษ

กรุณาวิเคราะห์บทถอดความการประชุมด้านล่าง และสกัดข้อมูลตามที่กำหนด

กฎที่ต้องปฏิบัติอย่างเคร่งครัด:
- ตอบด้วย JSON object ที่ถูกต้องเท่านั้น ห้ามมีข้อความ คำอธิบาย หรือ markdown ใดๆ นอกจาก JSON
- ห้ามใช้ ```json หรือ ``` ครอบ JSON
- หากไม่พบข้อมูลในส่วนใด ให้ใส่ค่าว่าง [] หรือ null แทนการคาดเดา
- สกัดข้อมูลจากบทถอดความเท่านั้น ห้ามเพิ่มข้อมูลที่ไม่มีในบทถอดความ
- หากบทถอดความมีทั้งภาษาไทยและภาษาอังกฤษ ให้สรุปเป็นภาษาไทย

โครงสร้าง JSON ที่ต้องการ:
{{
  "summary": "สรุปการประชุมอย่างละเอียด ครอบคลุมประเด็นสำคัญทั้งหมด (string)",
  "topics": ["หัวข้อสำคัญที่มีการพูดถึงในการประชุม (list of strings)"],
  "decisions": ["การตัดสินใจและข้อสรุปที่เกิดขึ้นในการประชุม (list of strings)"],
  "action_items": [
    {{
      "owner": "ชื่อผู้รับผิดชอบ หรือ null หากไม่ระบุ",
      "task_description": "รายละเอียดงานที่ต้องดำเนินการ",
      "due_date": "วันกำหนดส่งในรูปแบบ YYYY-MM-DD หรือ null หากไม่ระบุ"
    }}
  ],
  "issues": [
    {{
      "product": "ชื่อสินค้า โครงการ หรือระบบที่เกี่ยวข้อง หรือ null หากไม่ระบุ",
      "problem": "รายละเอียดปัญหาที่พบ",
      "solution": "แนวทางแก้ไขที่เสนอ หรือ null หากยังไม่มีแนวทาง"
    }}
  ]
}}

บทถอดความการประชุม:
{transcript}"""

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

    prompt = f"""คุณคือผู้เชี่ยวชาญด้านการถอดความเสียงที่มีความแม่นยำสูง เชี่ยวชาญทั้งภาษาไทยและภาษาอังกฤษ

คุณได้รับบทถอดความ 3 เวอร์ชันจากไฟล์เสียงเดียวกัน ซึ่งสร้างด้วยค่า temperature ที่แตกต่างกัน แต่ละเวอร์ชันอาจมีข้อผิดพลาด การตีความผิด หรือคำที่ขาดหายไป

หน้าที่ของคุณคือวิเคราะห์ทั้ง 3 เวอร์ชันและสร้างบทถอดความสุดท้ายที่ถูกต้องที่สุด

หลักการวิเคราะห์:
- ใช้ความเห็นตรงกันของทั้ง 3 เวอร์ชันเป็นเกณฑ์หลักในการตัดสิน
- หากสองเวอร์ชันตรงกันและหนึ่งเวอร์ชันต่างออกไป ให้ใช้เวอร์ชันที่ตรงกัน
- ตัดคำหรือประโยคที่ดูเหมือน hallucination ออก เช่น คำที่ไม่สอดคล้องกับบริบท หรือปรากฏเพียงเวอร์ชันเดียว
- รักษาคำศัพท์ภาษาอังกฤษที่ปรากฏในบทถอดความไว้ตามเดิม อย่าแปลหรือเปลี่ยน
- แก้ไขไวยากรณ์และการสะกดคำให้ถูกต้องโดยไม่เปลี่ยนความหมาย
- รักษาลำดับและโครงสร้างของการสนทนาตามที่ปรากฏในบทถอดความ
- หากทั้ง 3 เวอร์ชันไม่ตรงกันเลย ให้เลือกเวอร์ชันที่สมเหตุสมผลที่สุดตามบริบท

กฎที่ต้องปฏิบัติอย่างเคร่งครัด:
- ตอบด้วยบทถอดความสุดท้ายเท่านั้น
- ห้ามมีคำอธิบาย ความคิดเห็น หรือข้อความใดๆ นอกจากบทถอดความ
- ห้ามใช้ markdown, tag, หรือ formatting ใดๆ
- ห้ามเพิ่มเนื้อหาที่ไม่มีในบทถอดความต้นฉบับ

เวอร์ชันที่ 1:
{t1}

เวอร์ชันที่ 2:
{t2}

เวอร์ชันที่ 3:
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

def call_typhoon(prompt: str, max_tokens: int = 512) -> str:
    if not client:
        return ""
    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM Error in call_typhoon: {e}")
        return ""

def expand_search_query(query: str) -> str:
    """
    Rewrite the user's raw query into a richer, more specific version
    before it is embedded and sent to pgvector.

    Why this matters
    ----------------
    Short queries like "budget problem" or "ปัญหาการขาย" are ambiguous —
    the same words appear in many meetings in different contexts. By asking
    Typhoon to add likely intent words and domain context, the resulting
    embedding lands in a more specific region of the vector space, so the
    cosine search retrieves genuinely relevant chunks rather than any chunk
    that happens to contain the keyword.

    Falls back to the original query if the LLM call fails so search is
    never blocked by this step.
    """
    prompt = f"""คุณคือระบบปรับปรุงคำค้นหาสำหรับเครื่องมือค้นหาบันทึกการประชุม
หน้าที่ของคุณคือเขียนคำค้นหาของผู้ใช้ใหม่ให้มีความเฉพาะเจาะจงและชัดเจนยิ่งขึ้น

กฎที่ต้องปฏิบัติตามอย่างเคร่งครัด:
- ตอบเป็นภาษาไทยเสมอ แม้ว่าคำค้นหาต้นฉบับจะเป็นภาษาอังกฤษ
- เพิ่มคำที่เกี่ยวข้องกับบริบทหรือโดเมนเพื่อให้ความหมายชัดเจนขึ้น
- ห้ามเปลี่ยนความหมายหรือเพิ่มหัวข้อที่ไม่เกี่ยวข้อง
- ตอบเฉพาะคำค้นหาที่เขียนใหม่เท่านั้น ห้ามอธิบายหรือเพิ่มเครื่องหมายใดๆ

คำค้นหาต้นฉบับ: {query}

คำค้นหาที่ปรับปรุงแล้ว:"""

    try:
        response = call_typhoon(prompt, max_tokens=120)   # reuse your existing Typhoon wrapper
        rewritten = response.strip()
        # Sanity check: if the model returns something suspiciously long or empty, fall back
        if not rewritten or len(rewritten) > 400:
            return query
        return rewritten
    except Exception:
        return query   # silent fallback — search still works, just without expansion

def translate_for_embedding(text: str) -> str:
    """
    Translate a transcript chunk to the opposite language (Thai↔English)
    so the stored embedding captures both, improving cross-lingual retrieval.
    Fails silently — if translation fails the original text is still embedded.
    """
    prompt = f"""แปลข้อความต่อไปนี้เป็นภาษาอังกฤษหากเป็นภาษาไทย หรือแปลเป็นภาษาไทยหากเป็นภาษาอังกฤษ
    ตอบเฉพาะคำแปลเท่านั้น ห้ามอธิบายเพิ่มเติม

    ข้อความ: {text}

    คำแปล:"""
    try:
        return call_typhoon(prompt, max_tokens=300).strip()
    except Exception:
        return text


def expand_query_bilingual(query: str) -> str:
    """
    Produce a bilingual embedding text: original query + its translation.

    Why this matters
    ----------------
    bge-m3 is cross-lingual, so embedding a text that contains BOTH
    "scholarship" and "ทุนการศึกษา" places the query vector in a region
    of the vector space that is close to segments written in *either*
    language.  Without this, an English query misses Thai-only segments
    and vice-versa.

    Falls back to the original query string if the LLM call fails —
    the dense search still works, just without the cross-lingual boost.
    """
    try:
        translation = translate_for_embedding(query)
        # Only append if we got something different and not too long
        if translation and translation.strip() and translation.strip() != query.strip() and len(translation) < 400:
            return f"{query}\n{translation}"
    except Exception:
        pass
    return query