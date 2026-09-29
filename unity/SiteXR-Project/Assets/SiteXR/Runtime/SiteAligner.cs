// Two-point site alignment for construction AR (AR Foundation: iOS + Android).
//
// On site: aim the crosshair at your first layout mark, tap "Mark A", aim at
// the second mark, tap "Mark B". The model's CP_A / CP_B control points (made
// by blender-bridge/examples/site_anchors.py) snap onto those marks, and the
// model is locked to an AR anchor. The measured distance is checked against
// the plan so you know whether to trust the overlay.
//
// Setup: see unity/README.md.

using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

public class SiteAligner : MonoBehaviour
{
    const float InchesPerMeter = 39.3701f;

    [Tooltip("The model imported from Blender (must contain CP_A and CP_B).")]
    public GameObject modelPrefab;

    [Tooltip("On the XR Origin.")]
    public ARRaycastManager raycastManager;

    [Tooltip("On the XR Origin. Optional, but without it the model can drift.")]
    public ARAnchorManager anchorManager;

    [Tooltip("Warn when measured and plan distance differ by more than this.")]
    public float toleranceInches = 0.5f;

    [Tooltip("Size of one nudge step.")]
    public float nudgeInches = 0.125f;

    enum Step { MarkA, MarkB, Placed }

    static readonly List<ARRaycastHit> Hits = new List<ARRaycastHit>();

    Step step = Step.MarkA;
    bool aimingAtFloor;
    Pose aimPose;
    Vector3 pointA, pointB;
    GameObject model;
    GameObject anchor;
    Transform cpA, cpB;
    string status = "Aim the crosshair at mark A";
    bool warning;

    void Update()
    {
        if (raycastManager == null) return;
        var center = new Vector2(Screen.width / 2f, Screen.height / 2f);
        aimingAtFloor = raycastManager.Raycast(center, Hits, TrackableType.PlaneWithinPolygon);
        if (aimingAtFloor) aimPose = Hits[0].pose;
    }

    void Mark()
    {
        if (!aimingAtFloor) return;
        if (step == Step.MarkA)
        {
            pointA = aimPose.position;
            step = Step.MarkB;
            status = "A marked. Aim at mark B";
            warning = false;
        }
        else if (step == Step.MarkB)
        {
            pointB = aimPose.position;
            Align();
        }
    }

    void Align()
    {
        if (model == null) model = Instantiate(modelPrefab);
        cpA = FindDeep(model.transform, "CP_A");
        cpB = FindDeep(model.transform, "CP_B");
        if (cpA == null || cpB == null)
        {
            ResetAlignment();
            Fail("Model has no CP_A / CP_B. Run site_anchors.py in Blender and re-export.");
            return;
        }

        Vector3 planDir = Flat(cpB.position - cpA.position);
        Vector3 siteDir = Flat(pointB - pointA);
        if (siteDir.magnitude < 0.3f)
        {
            Fail("A and B are too close together. Mark two points at least 1 ft apart.");
            step = Step.MarkB;
            return;
        }

        // Yaw only: floors are level, so never tilt the model.
        model.transform.SetParent(null, true);
        float yaw = Vector3.SignedAngle(planDir, siteDir, Vector3.up);
        model.transform.rotation = Quaternion.AngleAxis(yaw, Vector3.up) * model.transform.rotation;
        model.transform.position += pointA - cpA.position;

        LockToAnchor();

        float plan = planDir.magnitude, site = siteDir.magnitude;
        float offInches = (site - plan) * InchesPerMeter;
        warning = Mathf.Abs(offInches) > toleranceInches;
        status = $"Plan {FtIn(plan)}   Measured {FtIn(site)}   ({(offInches >= 0 ? "+" : "-")}{Fraction(Mathf.Abs(offInches))}\")"
                 + (warning ? "\nMarks don't match the plan. Check them, or Reset." : "\nAligned on A, pointing at B.");
        step = Step.Placed;
    }

    void LockToAnchor()
    {
        if (anchor != null) Destroy(anchor);
        anchor = new GameObject("Site Anchor");
        anchor.transform.SetPositionAndRotation(cpA.position, Quaternion.LookRotation(Flat(cpB.position - cpA.position)));
        if (anchorManager != null && anchorManager.enabled)
            anchor.AddComponent<ARAnchor>();  // world-locks the anchor through AR tracking updates
        model.transform.SetParent(anchor.transform, true);
    }

    // along: + moves toward B. side: + moves toward the model's side of the
    // layout line (the model sits left of A -> B). Steps are nudgeInches.
    void Nudge(int along, int side, float degrees)
    {
        if (step != Step.Placed) return;
        Vector3 dir = Flat(cpB.position - cpA.position).normalized;
        Vector3 toModel = Vector3.Cross(dir, Vector3.up);  // left of dir (Unity is left-handed)
        float m = nudgeInches / InchesPerMeter;
        model.transform.position += dir * (along * m) + toModel * (side * m);
        if (degrees != 0) model.transform.RotateAround(cpA.position, Vector3.up, degrees);
    }

    void ResetAlignment()
    {
        if (model != null) Destroy(model);
        if (anchor != null) Destroy(anchor);
        model = null;
        anchor = null;
        step = Step.MarkA;
        status = "Aim the crosshair at mark A";
        warning = false;
    }

    void Fail(string message)
    {
        status = message;
        warning = true;
    }

    void OnGUI()
    {
        float u = Mathf.Max(Screen.height, Screen.width) / 60f;  // 1 UI unit, scales with screen
        var label = new GUIStyle(GUI.skin.label) { fontSize = (int)(u * 0.9f), wordWrap = true };
        var button = new GUIStyle(GUI.skin.button) { fontSize = (int)(u * 0.9f) };
        label.normal.textColor = warning ? new Color(1f, 0.45f, 0.35f) : Color.white;

        // Crosshair
        float cx = Screen.width / 2f, cy = Screen.height / 2f, len = u * 1.5f, t = Mathf.Max(2f, u / 8f);
        Color old = GUI.color;
        GUI.color = aimingAtFloor ? Color.green : Color.red;
        GUI.DrawTexture(new Rect(cx - len, cy - t / 2, len * 2, t), Texture2D.whiteTexture);
        GUI.DrawTexture(new Rect(cx - t / 2, cy - len, t, len * 2), Texture2D.whiteTexture);
        GUI.color = old;

        GUI.Box(new Rect(u * 0.5f, u * 0.5f, Screen.width - u, u * 3.2f), GUIContent.none);
        string aimHint = step == Step.Placed ? "" : aimingAtFloor ? "" : "\nMove the device slowly until the floor is found (crosshair turns green).";
        GUI.Label(new Rect(u, u * 0.7f, Screen.width - u * 2, u * 3f), status + aimHint, label);

        float bw = u * 7f, bh = u * 2.6f, y = Screen.height - bh - u;
        if (step != Step.Placed)
        {
            GUI.enabled = aimingAtFloor;
            if (GUI.Button(new Rect(cx - bw, y, bw * 2, bh), step == Step.MarkA ? "Mark A" : "Mark B", button)) Mark();
            GUI.enabled = true;
            return;
        }

        string n = Fraction(nudgeInches) + "\"";
        float sw = (Screen.width - u * 2) / 4f, y2 = y - bh - u * 0.4f;
        if (GUI.Button(new Rect(u, y2, sw - u * 0.2f, bh), "<- A " + n, button)) Nudge(-1, 0, 0);
        if (GUI.Button(new Rect(u + sw, y2, sw - u * 0.2f, bh), n + " B ->", button)) Nudge(1, 0, 0);
        if (GUI.Button(new Rect(u + sw * 2, y2, sw - u * 0.2f, bh), "Off line " + n, button)) Nudge(0, 1, 0);
        if (GUI.Button(new Rect(u + sw * 3, y2, sw - u * 0.2f, bh), "Onto line " + n, button)) Nudge(0, -1, 0);
        if (GUI.Button(new Rect(u, y, sw - u * 0.2f, bh), "Turn -0.1°", button)) Nudge(0, 0, -0.1f);
        if (GUI.Button(new Rect(u + sw, y, sw - u * 0.2f, bh), "Turn +0.1°", button)) Nudge(0, 0, 0.1f);
        if (GUI.Button(new Rect(u + sw * 2, y, sw - u * 0.2f, bh), model.activeSelf ? "Hide" : "Show", button)) model.SetActive(!model.activeSelf);
        if (GUI.Button(new Rect(u + sw * 3, y, sw - u * 0.2f, bh), "Reset", button)) ResetAlignment();
    }

    static Vector3 Flat(Vector3 v) => new Vector3(v.x, 0f, v.z);

    static Transform FindDeep(Transform root, string name)
    {
        if (root.name == name) return root;
        foreach (Transform child in root)
        {
            Transform found = FindDeep(child, name);
            if (found != null) return found;
        }
        return null;
    }

    // 4.8768 m -> 16' 0"
    static string FtIn(float meters)
    {
        float inches = Mathf.Round(meters * InchesPerMeter * 16f) / 16f;
        int feet = Mathf.FloorToInt(inches / 12f);
        return $"{feet}' {Fraction(inches - feet * 12f)}\"";
    }

    // 3.4375 -> 3 7/16 (nearest 1/16)
    static string Fraction(float inches)
    {
        int sixteenths = Mathf.RoundToInt(inches * 16f);
        int whole = sixteenths / 16, rem = sixteenths % 16, den = 16;
        while (rem != 0 && rem % 2 == 0) { rem /= 2; den /= 2; }
        if (rem == 0) return whole.ToString();
        return whole == 0 ? $"{rem}/{den}" : $"{whole} {rem}/{den}";
    }
}
