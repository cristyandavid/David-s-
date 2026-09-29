"""MCP server that lets Claude talk to Blender through the Claude Bridge add-on.

Run by Claude Code on the same computer as Blender:
    claude mcp add blender -- python /path/to/blender-bridge/mcp_server.py
"""

import json
import os
import socket

try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer

HOST = os.environ.get("BLENDER_BRIDGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("BLENDER_BRIDGE_PORT", "9876"))
TIMEOUT = float(os.environ.get("BLENDER_BRIDGE_TIMEOUT", "130"))

mcp = MCPServer("blender")


def send(payload):
    """Send one request to the Blender add-on and return its decoded reply."""
    try:
        with socket.create_connection((HOST, PORT), timeout=TIMEOUT) as sock:
            sock.sendall(json.dumps(payload).encode() + b"\n")
            buf = b""
            while b"\n" not in buf:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
    except ConnectionRefusedError:
        return {
            "status": "error",
            "message": (
                f"Blender is not listening on {HOST}:{PORT}. Open Blender, press N in "
                "the 3D viewport, go to the Claude tab and click Start Claude Bridge."
            ),
        }
    except OSError as exc:
        return {"status": "error", "message": f"Bridge connection failed: {exc}"}
    if not buf.strip():
        return {"status": "error", "message": "Blender closed the connection without replying"}
    return json.loads(buf.split(b"\n", 1)[0])


@mcp.tool()
def ping() -> dict:
    """Check that Blender is running with the Claude Bridge started."""
    return send({"type": "ping"})


@mcp.tool()
def get_scene_info() -> dict:
    """Summarize the current Blender scene: objects, transforms, materials, render engine."""
    return send({"type": "scene_info"})


@mcp.tool()
def get_object_info(name: str) -> dict:
    """Detailed info for one object: dimensions, materials, modifiers, mesh stats."""
    return send({"type": "object_info", "name": name})


@mcp.tool()
def execute_blender_code(code: str) -> dict:
    """Run Python inside Blender (bpy is pre-imported).

    Printed output is returned as stdout. Assign a JSON-serializable value to a
    variable named `result` to return it directly.
    """
    return send({"type": "exec", "code": code})


if __name__ == "__main__":
    mcp.run()
