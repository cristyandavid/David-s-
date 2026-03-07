import requests
from config import (
    OLLAMA_URL, OLLAMA_MODEL,
    USE_KIMI, KIMI_API_KEY, KIMI_MODEL, KIMI_URL,
    SYSTEM_PROMPT
)
from memory import list_memories

def build_context(user_text: str) -> str:
    memories = list_memories(limit=10)
    mem_text = '\n'.join(f'{k}: {v}' for k, v, _ in memories) if memories else 'None'
    return f"System:\n{SYSTEM_PROMPT}\n\nKnown memories:\n{mem_text}\n\nUser:\n{user_text}"

def call_llm(user_text: str) -> str:
    if USE_KIMI:
        return _call_kimi(user_text)
    return _call_ollama(user_text)

def _call_kimi(user_text: str) -> str:
    memories = list_memories(limit=10)
    mem_text = '\n'.join(f'{k}: {v}' for k, v, _ in memories) if memories else 'None'
    messages = [
        {'role': 'system', 'content': f"{SYSTEM_PROMPT}\n\nKnown memories:\n{mem_text}"},
        {'role': 'user',   'content': user_text},
    ]
    resp = requests.post(
        KIMI_URL,
        headers={'Authorization': f'Bearer {KIMI_API_KEY}', 'Content-Type': 'application/json'},
        json={'model': KIMI_MODEL, 'messages': messages},
        timeout=60
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content'].strip()

def _call_ollama(user_text: str) -> str:
    resp = requests.post(
        OLLAMA_URL,
        json={'model': OLLAMA_MODEL, 'prompt': build_context(user_text), 'stream': False},
        timeout=120
    )
    resp.raise_for_status()
    return resp.json().get('response', '').strip()

def parse_tool(llm_output: str):
    if not llm_output.startswith('TOOL:'):
        return None
    parts = [p.strip() for p in llm_output.replace('TOOL:', '', 1).split('|')]
    return (parts[0], parts[1:]) if parts else None
