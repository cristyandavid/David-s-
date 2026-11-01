"""Build the iPhone mini Duo case in Blender (bpy). Usage: python3 build_blend.py
Outputs duo_case_mini.blend + render_exploded_mini.png + render_assembled_mini.png"""
import os, math
os.environ["PHONE"] = "mini"
import bpy, bmesh
from mathutils import Vector
import duo_case as d

here = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
S = 0.001  # mm -> m

def mk(name, mf, color, rough=0.35, metal=0.0, coll=None):
    t = d.to_tm(mf)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v * S) for v in t.vertices], [], [tuple(f) for f in t.faces])
    me.update()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    mat = bpy.data.materials.new(name + "_mat"); mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    ob.data.materials.append(mat)
    # keep hard edges crisp, smooth the curved ones
    ob.modifiers.new("Normals", "WEIGHTED_NORMAL")
    return ob

back  = mk("Back_Shell",  d.back,  (0.045, 0.05, 0.06), 0.28)
front = mk("Front_Shell", d.front, (0.75, 0.16, 0.10), 0.28)
phone_mf = d.slab(d.rrect(d.W, d.H, d.R), d.FLOOR + d.CLR, d.FLOOR + d.CLR + d.T)
phone = mk("Phone_Reference", phone_mf, (0.05, 0.12, 0.30), 0.2, 0.6)
# glass screen face
for o in (back, front, phone):
    o.rotation_euler = (0, 0, 0)

# floor + world
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, -0.0005))
fl = bpy.context.object; fl.name = "Floor"
fm = bpy.data.materials.new("Floor"); fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.56, 0.6, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
fl.data.materials.append(fm)
sc.world = bpy.data.worlds.new("W"); sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.7, 0.75, 0.85, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.25

def light(name, loc, energy, size):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size
    lo = bpy.data.objects.new(name, ld); lo.location = loc; sc.collection.objects.link(lo)
    direction = Vector((0, 0, 0.03)) - Vector(loc)
    lo.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
light("Key", (0.25, -0.3, 0.35), 14, 0.3)
light("Fill", (-0.3, -0.15, 0.2), 5, 0.4)
light("Rim", (0.0, 0.3, 0.25), 8, 0.3)

cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 85
cam = bpy.data.objects.new("Cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam

def look(target, loc):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

sc.render.engine = "CYCLES"; sc.cycles.samples = 32; sc.cycles.device = "CPU"
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1400, 900
try:
    sc.view_settings.view_transform = "AgX"
except Exception: pass

def shot(path):
    sc.render.filepath = os.path.join(here, path); bpy.ops.render.render(write_still=True)

# exploded
front.location.z = 0.045; phone.location.z = 0.020
phone.hide_render = False
look((0, 0.0, 0.025), (0.0, -0.40, 0.30))
shot("render_exploded_mini.png")
# assembled (phone hidden)
front.location.z = 0; phone.hide_render = True; phone.hide_viewport = True
look((0, 0, 0.005), (0.05, -0.32, 0.26))
shot("render_assembled_mini.png")
# leave the .blend in the exploded layout
front.location.z = 0.045; phone.location.z = 0.020; phone.hide_render = phone.hide_viewport = False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(here, "duo_case_mini.blend"))
print("saved")
