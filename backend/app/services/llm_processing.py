import os
import json
from openai import OpenAI

TYPHOON_API_KEY = os.getenv("TYPHOON_API_KEY", "")
# SCB 10X Typhoon uses an OpenAI-compatible API
TYPHOON_BASE_URL = os.getenv("TYPHOON_BASE_URL", "https://api.opentyphoon.ai/v1") 

client = OpenAI(api_key=TYPHOON_API_KEY, base_url=TYPHOON_BASE_URL) if TYPHOON_API_KEY else None

def extract_meeting_info(transcript: str):
    """
    Extracts summary, action items, and issues from the transcript using LLM.
    """
    if not client:
        return _mock_extraction(transcript)
        
    prompt = f"""
    You are an AI meeting assistant. Analyze the following meeting transcript and extract the requested information.
    Format your response as a JSON object with the following keys:
    - summary: A brief summary of the meeting.
    - topics: A list of important discussion topics (strings).
    - decisions: A list of decisions and conclusions (strings).
    - action_items: A list of objects, each containing 'owner', 'task_description', and 'due_date' (ISO format or null).
    - issues: A list of objects, each containing 'product', 'problem', and 'solution' (or null if no solution proposed).

    Transcript:
    {transcript}
    """
    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"LLM Error: {e}")
        return _mock_extraction(transcript)

def qa_meeting(context: str, query: str):
    """
    Answers a question based on the meeting context.
    """
    if not client:
        return "I am a mock LLM. I don't have the real answer since the API key is missing."
        
    prompt = f"""
    Answer the user's question based strictly on the provided context. If the answer is not in the context, say so.
    
    Context:
    {context}
    
    Question: {query}
    """
    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Error: {e}")
        return "Error calling LLM."

def _mock_extraction(transcript: str):
    return {
        "summary": "This is a mock summary. The actual LLM call failed or the API key was not provided.",
        "topics": ["Mock Topic 1", "Mock Topic 2"],
        "decisions": ["Proceed with mock implementation"],
        "action_items": [
            {"owner": "Developer", "task_description": "Set TYPHOON_API_KEY", "due_date": None}
        ],
        "issues": [
            {"product": "System", "problem": "LLM API Key missing", "solution": "Add key to docker-compose.yml"}
        ]
    }
