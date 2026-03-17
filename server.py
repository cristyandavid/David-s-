import os
import json
from flask import Flask, request, Response, send_file
import anthropic

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are Claude, powering the Claude Engineering Console.

Core directive: Optimize for tomorrow being easier than today.

You help with:
- /check [scope]: Risk audit — fragile areas, tech debt hotspots, silent failure risks
- /plan [goal]: Propose 1–3 concrete bounded improvements with expected impact
- /execute: Execute the most recently agreed plan item. No scope creep.

Behavior defaults:
- Read before editing. Understand before suggesting.
- Smallest change that achieves the goal.
- No speculative refactors, no unsolicited features.
- Security first: flag injection, auth, and data exposure risks immediately.
- When uncertain, ask. One targeted question beats three wrong assumptions."""


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages", [])

    def generate():
        try:
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=messages,
                thinking={"type": "adaptive"},
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            yield f"data: {json.dumps({'type': 'text', 'text': event.delta.text})}\n\n"
                        elif event.delta.type == "thinking_delta":
                            yield f"data: {json.dumps({'type': 'thinking', 'text': event.delta.thinking})}\n\n"
                    elif event.type == "message_stop":
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except anthropic.AuthenticationError:
            yield f"data: {json.dumps({'type': 'error', 'text': 'Invalid API key. Check ANTHROPIC_API_KEY.'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Claude Engineering Console → http://localhost:{port}")
    app.run(debug=False, port=port, threaded=True)
