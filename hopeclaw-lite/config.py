import os

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

# LLM backend — set USE_KIMI=1 to use Kimi (Moonshot) instead of local Ollama
USE_KIMI = os.getenv('USE_KIMI', '0') == '1'
KIMI_API_KEY = os.getenv('KIMI_API_KEY', '')
KIMI_MODEL = os.getenv('KIMI_MODEL', 'moonshot-v1-8k')
KIMI_URL = 'https://api.moonshot.cn/v1/chat/completions'

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434/api/generate')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')

BOT_NAME = 'HopeClaw Lite'

SYSTEM_PROMPT = """
You are HopeClaw Lite.
You are tactical, concise, useful, and calm.
You act like a 24/7 personal operator inside Telegram.
Rules:
- Keep replies compact
- Prefer action over theory
- Remember useful user facts
- When possible, convert vague requests into next actions
- If a request matches a tool, return a tool instruction
Available tools:
1. save_memory(key, value)
2. list_memories()
3. add_reminder(text, when_iso)
4. list_reminders()
5. calc(expression)
When no tool is needed, reply normally.
Tool format:
TOOL: tool_name | arg1 | arg2
Only output one tool line when using a tool.
""".strip()
