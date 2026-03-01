"""
Smart contract generator — web preview server.

Usage:
    python preview.py [--port 8080]

Opens a browser UI for generating and previewing contract source.
No external dependencies — stdlib only.
"""

import argparse
import html
import http.server
import urllib.parse
from src.generator import generate, SUPPORTED_TYPES

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Smart Contract Generator</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: system-ui, sans-serif;
      background: #0f0f11;
      color: #e2e2e6;
      margin: 0;
      padding: 2rem;
    }}
    h1 {{ font-size: 1.25rem; margin: 0 0 1.5rem; color: #a78bfa; letter-spacing: .03em; }}
    form {{
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
      align-items: flex-end;
      margin-bottom: 1.5rem;
    }}
    label {{ display: flex; flex-direction: column; gap: .3rem; font-size: .85rem; color: #9ca3af; }}
    input, select {{
      background: #1c1c24;
      border: 1px solid #2e2e3a;
      border-radius: 6px;
      color: #e2e2e6;
      padding: .45rem .75rem;
      font-size: .9rem;
      outline: none;
    }}
    input:focus, select:focus {{ border-color: #a78bfa; }}
    button {{
      background: #7c3aed;
      color: #fff;
      border: none;
      border-radius: 6px;
      padding: .5rem 1.25rem;
      font-size: .9rem;
      cursor: pointer;
    }}
    button:hover {{ background: #6d28d9; }}
    .output {{
      background: #1c1c24;
      border: 1px solid #2e2e3a;
      border-radius: 8px;
      padding: 1.25rem 1.5rem;
    }}
    .output-label {{
      font-size: .75rem;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: .08em;
      margin-bottom: .75rem;
    }}
    pre {{
      margin: 0;
      font-family: "JetBrains Mono", "Fira Code", monospace;
      font-size: .88rem;
      line-height: 1.65;
      white-space: pre-wrap;
      word-break: break-word;
      color: #c4b5fd;
    }}
    .error {{ color: #f87171; }}
    .meta {{ font-size: .78rem; color: #4b5563; margin-top: 1rem; }}
  </style>
</head>
<body>
  <h1>&#9881; Smart Contract Generator</h1>
  <form method="get">
    <label>Type
      <select name="type">
        {type_options}
      </select>
    </label>
    <label>Name
      <input name="name" value="{name_val}" placeholder="MyContract" required>
    </label>
    <label>Symbol
      <input name="symbol" value="{symbol_val}" placeholder="optional">
    </label>
    <label>Owner address
      <input name="owner" value="{owner_val}" placeholder="optional">
    </label>
    <button type="submit">Generate</button>
  </form>
  {output_block}
  <p class="meta">Running on stdlib http.server &mdash; for development only.</p>
</body>
</html>"""


def _type_options(selected: str) -> str:
    return "\n        ".join(
        f'<option value="{t}"{"  selected" if t == selected else ""}>{t.upper()}</option>'
        for t in SUPPORTED_TYPES
    )


def _render(params: dict) -> str:
    contract_type = params.get("type", SUPPORTED_TYPES[0])
    name = params.get("name", "").strip()
    symbol = params.get("symbol", "").strip()
    owner = params.get("owner", "").strip()

    if name:
        try:
            source = generate(contract_type, {"name": name, "symbol": symbol, "owner": owner})
            output_block = (
                '<div class="output">'
                '<div class="output-label">Generated Solidity</div>'
                f"<pre>{html.escape(source)}</pre>"
                "</div>"
            )
        except ValueError as exc:
            output_block = f'<div class="output"><pre class="error">{html.escape(str(exc))}</pre></div>'
    else:
        output_block = ""

    return _HTML_TEMPLATE.format(
        type_options=_type_options(contract_type),
        name_val=html.escape(name),
        symbol_val=html.escape(symbol),
        owner_val=html.escape(owner),
        output_block=output_block,
    )


class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quieter logs
        print(f"  {self.address_string()} {fmt % args}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = dict(urllib.parse.parse_qsl(parsed.query))
        body = _render(params).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Web preview for smart-contract-generator.")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    addr = ("", args.port)
    with http.server.HTTPServer(addr, _Handler) as server:
        print(f"Preview running at http://localhost:{args.port}  (Ctrl+C to stop)")
        server.serve_forever()


if __name__ == "__main__":
    main()
