# Home setup checklist

Everything is in this repo. On the Mac, in Terminal:

```bash
git clone https://github.com/cristyandavid/David-s-.git ~/David-s-
cd ~/David-s- && ./setup-mac.sh
```

The script installs what it can (Python, Blender, Unity Hub, the Blender
bridge) and ends with a list of anything left to do by hand. Re-run it after
each manual step until the list is empty.

## 1. Manual installs (start these first, they're big downloads)

- [ ] **Xcode** from the App Store (~15 GB). Open it once and accept the licence.
- [ ] **Unity 6 LTS**: Unity Hub → sign in (free Unity account) → Installs →
      Install Editor → Unity 6 LTS, tick **iOS Build Support**.
- [ ] **Claude Code**: see https://code.claude.com/docs, then re-run `./setup-mac.sh`
      so it connects Blender to Claude.

## 2. Quick AR test, no Unity needed (2 min)

- [ ] On your iPhone/iPad, open `blender-bridge/examples/ar/stud_wall.usdz` on GitHub
      → Download → open it from Files. The 16 ft wall should stand upright at full size.

## 3. Blender + Claude (5 min)

- [ ] Open Blender → press **N** in the 3D view → **Claude** tab → **Start Claude Bridge**.
- [ ] Terminal: `claude remote-control` (then you can also drive it from the Claude app).
- [ ] Say **"ping Blender"**. You should get `pong`.
- [ ] Say **"run examples/stud_wall.py, site_anchors.py and export_ar.py in Blender"**.
      The AR files land on your Desktop.

## 4. Unity AR app on the iPad (30–45 min the first time)

- [ ] Unity Hub → **Add** → **Add project from disk** → `~/David-s-/unity/SiteXR-Project`.
- [ ] Open it and wait. The Console should show `site model OK`, then
      `AR packages installed`, then `SiteXR setup: scene OK`.
- [ ] Plug in the iPad → File → **Build And Run** → in Xcode set *Team* to your
      Apple ID → ▶. First time on the iPad: Settings → General → VPN & Device
      Management → trust your Apple ID.

## 5. Try it at home before the site

- [ ] Put two tape marks on the garage floor **exactly 16' 0" apart** (A on the left).
- [ ] Open SiteXR → sweep the floor until the crosshair is green → aim at A → **Mark A**
      → aim at B → **Mark B**.
- [ ] The banner should read about `Plan 16' 0"  Measured 16' 0"`, and the wall should
      stand on the line between your marks.

If anything shows a red error, copy it to Claude. Details:
[`blender-bridge/README.md`](blender-bridge/README.md) · [`unity/README.md`](unity/README.md)
