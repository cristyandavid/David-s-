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

| File (in `SiteXR-Project/Assets/SiteXR/`) | Job |
|------|-----|
| `Runtime/SiteAligner.cs` | On-site app: crosshair, Mark A / Mark B, snap + anchor, tape check, nudge (1/8", 0.1°), hide/show, reset |
| `Editor/SiteModelImporter.cs` | Imports anything in `Assets/Site Models` at real scale with Blender axes fixed, and checks CP_A / CP_B |
| `Editor/SiteXRBootstrap.cs` | First open: installs the newest AR Foundation + ARKit for your Unity version |
| `Setup/SiteXRSetup.cs` | First open: builds the AR scene, enables ARKit, sets iOS camera permission + bundle ID, switches to iOS |

## Open the project

**Needs:** Unity 6 LTS (or 2022.3 LTS) with **iOS Build Support**, Xcode, and an
Apple ID. `../setup-mac.sh` installs Unity Hub and checks the rest.

1. Unity Hub → **Add** → **Add project from disk** → pick `unity/SiteXR-Project`.
   If asked which editor, pick Unity 6.
2. Open it and watch the Console (Window → General → Console). First open takes
   a few minutes:
   - `site model OK. CP_A -> CP_B = 4.877 m (16' 0.00")`: the wall imported at real scale
   - `SiteXR: installing AR Foundation + ARKit...` then `AR packages installed`
   - `SiteXR setup:` with `scene OK`, `ARKit enabled` and `iOS build target active`
3. **Build**: plug in your iPad/iPhone, then File → Build And Run. In Xcode, pick your
   Apple ID under *Signing & Capabilities → Team* and press ▶. On the device,
   trust the developer in Settings → General → VPN & Device Management the first time.

To use your own model, drop its `.fbx` into `Assets/Site Models` and drag it into
the *Site Aligner* object's **Model Prefab** slot in `Assets/Scenes/Site.unity`.

**Status:** none of this has been run in Unity yet. It's syntax-checked, and the
alignment math has been audited by hand (yaw, scale, imperial rounding — all
confirmed correct). If a line in the Console says something failed, it also says
the one manual fix (e.g. tick ARKit in XR Plug-in Management). Paste any red
errors to Claude.

<details><summary>Manual setup (if the automatic setup fails)</summary>

1. Window → Package Manager → Unity Registry: install *AR Foundation* and *Apple ARKit XR Plugin*.
2. Project Settings → XR Plug-in Management → iOS tab: tick *ARKit*.
   Player → iOS → *Camera Usage Description*: "Camera is used for AR".
3. New empty scene: GameObject → XR → *AR Session*, and GameObject → XR → *XR Origin (Mobile AR)*.
   On the XR Origin add *AR Plane Manager*, *AR Raycast Manager*, *AR Anchor Manager*.
4. Empty GameObject → add *Site Aligner* → drag in the Raycast Manager, Anchor Manager and
   `Assets/Site Models/stud_wall.fbx`.
5. Save the scene, add it in Build Settings, switch platform to iOS.
</details>

### Android build (optional)

The project targets iOS out of the box. For Android:
- Player Settings → *Minimum API Level* 24+, *Scripting Backend* IL2CPP, *ARM64* ticked (ARCore requires it).
- Player Settings → *Graphics APIs*: keep *OpenGLES3* (remove *Vulkan* if your ARCore version predates Vulkan support).
- Add the *Google ARCore XR Plugin* and tick *ARCore* on the Android tab of XR Plug-in Management.
- File → Build Settings → *Android* → *Build and Run*.

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
