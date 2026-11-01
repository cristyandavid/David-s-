"""Show the 3D view full screen for a projector. Run it again to go back.

Frames whatever is selected (or the whole model if nothing is), maximizes the 3D
view with its side panels hidden, and toggles Blender's window to full screen.
Run it in Blender's Text Editor. Move the second Blender window to the projector
first if you use two displays.
"""

import bpy

wm = bpy.context.window_manager
window = next((w for w in wm.windows), None)
area = next((a for w in wm.windows for a in w.screen.areas if a.type == "VIEW_3D"), None)
if window is None or area is None:
    raise RuntimeError("No 3D view found: switch to the Layout or Modeling workspace")

region = next(r for r in area.regions if r.type == "WINDOW")
with bpy.context.temp_override(window=window, area=area, region=region):
    selected = any(o.select_get() for o in bpy.context.view_layer.objects)
    (bpy.ops.view3d.view_selected if selected else bpy.ops.view3d.view_all)()
    bpy.ops.screen.screen_full_area(use_hide_panels=True)

with bpy.context.temp_override(window=window):
    bpy.ops.wm.window_fullscreen_toggle()
print("Full screen on. Run present_view.py again, or press Ctrl+Space, to leave.")
