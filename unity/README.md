# SiteXR: construction AR in Unity

Put a Blender model on the job site, lined up with your real layout marks.

```
Blender                               Unity (iPad / iPhone / Android)
stud_wall.py  → build the model
site_anchors.py → CP_A, CP_B on the     Aim at mark A → "Mark A"
  layout line (chalk line)              Aim at mark B → "Mark B"
export_ar.py  → .fbx (origin = CP_A) →  Model snaps onto the marks, is locked to
                                        an AR anchor, and the A–B distance is
                                        checked against the plan
```

| File | Job |
|------|-----|
| `SiteXR/Runtime/SiteAligner.cs` | On-site app: crosshair, Mark A / Mark B, snap + anchor, tape check, nudge (1/8", 0.1°), hide/show, reset |
| `SiteXR/Editor/SiteModelImporter.cs` | Imports anything in a `Site Models` folder at real scale with Blender axes fixed, and checks CP_A / CP_B |

## One-time Unity setup

Tested against: nothing yet. This code has only been syntax-checked and its
alignment math simulated. Expect to fix small things on the first build.
Written for Unity 2022.3 LTS or Unity 6 with AR Foundation 5 or 6.

1. **New project** with the *3D (URP)* or *3D* template.
2. **Packages** (Window → Package Manager → Unity Registry): *AR Foundation*,
   plus *Apple ARKit XR Plugin* (iPhone/iPad) and/or *Google ARCore XR Plugin* (Android).
3. **XR** (Project Settings → XR Plug-in Management): tick *ARKit* on the iOS
   tab and/or *ARCore* on the Android tab.
   iOS also needs Player Settings → *Camera Usage Description*, e.g. "Camera is used for AR".
4. **Copy** this repo's `unity/SiteXR` folder into your project's `Assets/`.
5. **Scene**: delete the Main Camera, then add GameObject → XR → *AR Session*
   and GameObject → XR → *XR Origin (Mobile AR)* (the name varies a little by version).
   On the XR Origin, add components *AR Plane Manager*, *AR Raycast Manager* and *AR Anchor Manager*.
6. **Aligner**: create an empty GameObject, add *Site Aligner*, and drag in the
   XR Origin's *AR Raycast Manager* and *AR Anchor Manager*.
7. **Model**: make a folder `Assets/Site Models`, drop in the `.fbx` from
   `export_ar.py` (try `blender-bridge/examples/ar/stud_wall.fbx`). The Console should
   say `site model OK. CP_A -> CP_B = 4.877 m (16' 0.00")`. Drag the model into
   Site Aligner's *Model Prefab* slot.
8. **Build** to your iPad/iPhone (File → Build Settings → iOS → Build, then run from
   Xcode) or Android.

## On site

1. **Mark the layout.** Snap the chalk line for the plate, and put a clear mark
   (an X in paint or tape) at each end. These are A and B. In Blender, CP_A is the
   left end when you face the wall from the chalk-line side, and the wall stands on
   the far side of the line.
2. **Scan the floor.** Open the app and sweep the device slowly over the floor
   until the crosshair turns green.
3. **Mark A, Mark B.** Hold the crosshair right on each mark and tap. Get close:
   1–2 m away is more accurate than across the room.
4. **Read the check.** The banner shows plan vs measured distance. Red means the
   marks and the plan disagree by more than ½". Re-check your marks or Reset.
5. **Fine-tune** with the nudge buttons if needed (1/8" steps, 0.1° turns).

Further apart is better: over a 16 ft line, a ½" error at one end twists the
model by about 0.15°.

## How accurate is it?

Phone and tablet AR is typically good to **about ½"–1½"** close to the marks,
and drifts further away and over time. iPads and iPhones with LiDAR are
noticeably better. Use the overlay to **check and visualize** layout, openings
and clashes. Don't use it in place of a tape and a laser for final layout. If
the model creeps, Reset and re-mark.

## Other models

Anything built in Blender works: run `site_anchors.py`, look at where CP_A and
CP_B landed, and move them onto any two points you can find on site (slab
corners, grid-line marks, anchor bolts). Then run `export_ar.py`.
