"""Blender animation of the iPhone Duo case folding/unfolding.
Usage: python3 animate_duo.py [--test]   -> duo_case_anim.blend, frames/, duo_fold.mp4, duo_fold.gif
Front shell + front phone half are parented to a hinge pivot at the Duo hinge axis and keyframed 0->180 deg."""
import os, sys, math, subprocess, shutil
import bpy
from mathutils import Vector
import duo_fold_case as d

TEST = "--test" in sys.argv
here = os.path.dirname(os.path.abspath(__file__))
S = 0.001
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def mk(name, mf, color, rough=0.3, metal=0.0, alpha=1.0):
    t = d.to_tm(mf)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v * S) for v in t.vertices], [], [tuple(f) for f in t.faces]); me.update()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    ob.data.materials.append(mat)
    ob.modifiers.new("N", "WEIGHTED_NORMAL")
    return ob

clipbox = d.box(d.HX, 100, -100, 100, -10, 20)
back  = mk("Back_Shell",  d.back,  (0.04, 0.045, 0.055), 0.28)
front = mk("Front_Shell", d.front, (0.85, 0.30, 0.04), 0.28)
phone_b = mk("Phone_Back_Half",  d.slab(d.rrect(d.PW, d.PL, d.PR), 0, d.HALF) ^ clipbox, (0.07, 0.10, 0.20), 0.2, 0.7)
phone_f = mk("Phone_Front_Half", d.slab(d.rrect(d.PW, d.PL, d.PR), d.PT - d.HALF, d.PT) ^ clipbox, (0.07, 0.10, 0.20), 0.2, 0.7)

# hinge pivot (empty) at the hinge axis; front half + shell ride on it
piv = bpy.data.objects.new("Hinge_Pivot", None); sc.collection.objects.link(piv)
piv.location = (d.HX * S, 0, d.SEAM * S)
bpy.context.view_layer.update()
for o in (front, phone_f):
    o.parent = piv; o.matrix_parent_inverse = piv.matrix_world.inverted()

# floor, world, lights
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, -0.0021)); fl = bpy.context.object
fm = bpy.data.materials.new("Floor"); fm.use_nodes = True
fb = fm.node_tree.nodes["Principled BSDF"]; fb.inputs["Base Color"].default_value = (0.22, 0.23, 0.26, 1); fb.inputs["Roughness"].default_value = 0.55
fl.data.materials.append(fm)
sc.world = bpy.data.worlds.new("W"); sc.world.use_nodes = True
bg = sc.world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.62, 0.67, 0.78, 1); bg.inputs[1].default_value = 0.12
def light(n, loc, e, size, target=(-0.02, 0, 0.005)):
    ld = bpy.data.lights.new(n, "AREA"); ld.energy = e; ld.size = size
    lo = bpy.data.objects.new(n, ld); lo.location = loc; sc.collection.objects.link(lo)
    lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
light("Key", (0.12, -0.35, 0.40), 11, 0.45); light("Fill", (-0.35, -0.2, 0.25), 3, 0.5); light("Rim", (-0.05, 0.35, 0.3), 6, 0.4)

# camera rig: pans with the opening phone, slow orbit
rig = bpy.data.objects.new("CamRig", None); sc.collection.objects.link(rig)
cd = bpy.data.cameras.new("Cam"); cd.lens = 70
cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
cam.parent = rig; cam.location = (0.0, -0.36, 0.30)
tr = cam.constraints.new("TRACK_TO"); tr.target = rig; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"

# timeline (24 fps): hold 12, open 36, hold 18, close 36, hold 12  = 114 frames
sc.render.fps = 24
F = dict(h0=1, open0=13, open1=49, h1=67, close1=103, end=114)
sc.frame_start, sc.frame_end = 1, F["end"]
piv.rotation_euler = (0, 0, 0)
for f, a in ((F["h0"], 0), (F["open0"], 0), (F["open1"], 180), (F["h1"], 180), (F["close1"], 0), (F["end"], 0)):
    piv.rotation_euler.y = -math.radians(a); piv.keyframe_insert("rotation_euler", index=1, frame=f)
    rig.location = (-0.040 * (a / 180), 0, 0.03 * math.sin(math.radians(a)) + 0.004)
    rig.keyframe_insert("location", frame=f)
    rig.rotation_euler = (0, 0, math.radians(-12 + 10 * (a / 180)) )
    rig.keyframe_insert("rotation_euler", frame=f)
# camera distance grows as the phone opens
cam.location = (0.0, -0.42, 0.34); cam.keyframe_insert("location", frame=F["open0"])
cam.location = (0.0, -0.56, 0.44); cam.keyframe_insert("location", frame=F["open1"])
cam.keyframe_insert("location", frame=F["h1"])
cam.location = (0.0, -0.42, 0.34); cam.keyframe_insert("location", frame=F["close1"])

sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.use_denoising = True
sc.cycles.samples = 8 if TEST else 16
try: sc.view_settings.view_transform = "AgX"
except Exception: pass
sc.render.resolution_x, sc.render.resolution_y = (640, 400) if TEST else (800, 500)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(here, "duo_case_anim.blend"))

fr = os.path.join(here, "frames"); shutil.rmtree(fr, ignore_errors=True); os.makedirs(fr)
sc.render.image_settings.file_format = "PNG"
frames = [1, 30, 49, 90] if TEST else range(1, F["end"] + 1)
for f in frames:
    sc.frame_set(f); sc.render.filepath = os.path.join(fr, f"f{f:04d}.png"); bpy.ops.render.render(write_still=True)
print("rendered", len(list(frames)))
