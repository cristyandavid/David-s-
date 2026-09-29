"""Claude Bridge — Blender add-on.

Runs a small TCP server on 127.0.0.1 so a local Claude session (through
mcp_server.py) can inspect the scene and run Python inside Blender.

Protocol: one JSON object per line in each direction.
  request:  {"type": "ping" | "scene_info" | "object_info" | "exec", ...}
  response: {"status": "ok", "result": ...} or {"status": "error", "message": ...}

SECURITY: "exec" runs arbitrary Python with your user's permissions.
The server only binds to localhost and is off until you press Start.
"""

bl_info = {
    "name": "Claude Bridge",
    "author": "cristyandavid",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Claude",
    "description": "Local socket bridge so Claude can control Blender",
    "category": "Development",
}

import contextlib
import io
import json
import queue
import socket
import threading
import traceback

import bpy

HOST = "127.0.0.1"
DEFAULT_PORT = 9876
JOB_TIMEOUT = 120.0  # seconds a client waits for Blender's main thread

# bpy is not thread-safe: socket threads queue jobs, a timer runs them.
_jobs = queue.Queue()
_server = None


def _vec(v):
    return [round(x, 4) for x in v]


def _object_summary(obj):
    return {
        "name": obj.name,
        "type": obj.type,
        "location": _vec(obj.location),
        "rotation_euler": _vec(obj.rotation_euler),
        "scale": _vec(obj.scale),
        "visible": obj.visible_get(),
        "parent": obj.parent.name if obj.parent else None,
    }


def _scene_info(_req):
    scene = bpy.context.scene
    return {
        "scene": scene.name,
        "frame_current": scene.frame_current,
        "frame_range": [scene.frame_start, scene.frame_end],
        "render_engine": scene.render.engine,
        "object_count": len(scene.objects),
        "objects": [_object_summary(o) for o in list(scene.objects)[:200]],
        "materials": [m.name for m in bpy.data.materials][:200],
    }


def _object_info(req):
    name = req.get("name", "")
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"No object named {name!r}")
    info = _object_summary(obj)
    info["dimensions"] = _vec(obj.dimensions)
    info["materials"] = [s.material.name for s in obj.material_slots if s.material]
    info["modifiers"] = [m.type for m in obj.modifiers]
    if obj.type == "MESH":
        mesh = obj.data
        info["mesh"] = {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "polygons": len(mesh.polygons),
        }
    return info


def _exec(req):
    code = req.get("code", "")
    namespace = {"bpy": bpy, "__name__": "__claude__"}
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exec(compile(code, "<claude>", "exec"), namespace)
    result = namespace.get("result")
    try:
        json.dumps(result)
    except TypeError:
        result = repr(result)
    return {"stdout": stdout.getvalue(), "result": result}


HANDLERS = {
    "ping": lambda _req: "pong",
    "scene_info": _scene_info,
    "object_info": _object_info,
    "exec": _exec,
}


def _dispatch(req):
    handler = HANDLERS.get(req.get("type"))
    if handler is None:
        return {"status": "error", "message": f"Unknown request type: {req.get('type')!r}"}
    try:
        return {"status": "ok", "result": handler(req)}
    except Exception as exc:
        return {
            "status": "error",
            "message": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }


def _process_jobs():
    while True:
        try:
            req, out = _jobs.get_nowait()
        except queue.Empty:
            break
        out.put(_dispatch(req))
    return 0.05 if _server is not None else None


class BridgeServer:
    def __init__(self, port):
        self.port = port
        self._stop = threading.Event()
        self._sock = None
        self._thread = None

    def start(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((HOST, self.port))
        self._sock.listen(4)
        self._sock.settimeout(1.0)
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._sock:
            self._sock.close()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _accept_loop(self):
        while not self._stop.is_set():
            try:
                conn, _addr = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    def _handle_client(self, conn):
        buf = b""
        with conn:
            while not self._stop.is_set():
                try:
                    chunk = conn.recv(65536)
                except OSError:
                    return
                if not chunk:
                    return
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if line.strip():
                        conn.sendall(self._respond(line) + b"\n")

    def _respond(self, line):
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            resp = {"status": "error", "message": f"Bad JSON: {exc}"}
        else:
            out = queue.Queue(maxsize=1)
            _jobs.put((req, out))
            try:
                resp = out.get(timeout=JOB_TIMEOUT)
            except queue.Empty:
                resp = {"status": "error", "message": "Timed out waiting for Blender"}
        return json.dumps(resp).encode()


class CLAUDE_OT_bridge_start(bpy.types.Operator):
    bl_idname = "claude.bridge_start"
    bl_label = "Start Claude Bridge"

    def execute(self, context):
        global _server
        if _server is not None:
            self.report({"INFO"}, "Bridge already running")
            return {"CANCELLED"}
        server = BridgeServer(context.scene.claude_bridge_port)
        try:
            server.start()
        except OSError as exc:
            self.report({"ERROR"}, f"Could not start bridge: {exc}")
            return {"CANCELLED"}
        _server = server
        bpy.app.timers.register(_process_jobs, persistent=True)
        self.report({"INFO"}, f"Claude Bridge listening on {HOST}:{server.port}")
        return {"FINISHED"}


class CLAUDE_OT_bridge_stop(bpy.types.Operator):
    bl_idname = "claude.bridge_stop"
    bl_label = "Stop Claude Bridge"

    def execute(self, context):
        _stop_server()
        self.report({"INFO"}, "Claude Bridge stopped")
        return {"FINISHED"}


class CLAUDE_PT_bridge(bpy.types.Panel):
    bl_label = "Claude Bridge"
    bl_idname = "CLAUDE_PT_bridge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Claude"

    def draw(self, context):
        layout = self.layout
        if _server is None:
            layout.prop(context.scene, "claude_bridge_port")
            layout.operator("claude.bridge_start", icon="PLAY")
        else:
            layout.label(text=f"Running on {HOST}:{_server.port}", icon="LINKED")
            layout.operator("claude.bridge_stop", icon="PAUSE")


def _stop_server():
    global _server
    if _server is not None:
        _server.stop()
        _server = None
    if bpy.app.timers.is_registered(_process_jobs):
        bpy.app.timers.unregister(_process_jobs)


CLASSES = (CLAUDE_OT_bridge_start, CLAUDE_OT_bridge_stop, CLAUDE_PT_bridge)


def register():
    bpy.types.Scene.claude_bridge_port = bpy.props.IntProperty(
        name="Port", default=DEFAULT_PORT, min=1024, max=65535
    )
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    _stop_server()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.claude_bridge_port


if __name__ == "__main__":
    register()
