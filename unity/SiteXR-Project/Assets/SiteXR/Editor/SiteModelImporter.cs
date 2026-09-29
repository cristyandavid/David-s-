// Import settings for models exported by blender-bridge/examples/export_ar.py.
// Applies to any .fbx / .glb dropped into a folder named "Site Models":
// real-world scale (1 unit = 1 m), Blender axes baked in (no -90° root
// rotation), no cameras / lights / animation. Then checks for CP_A / CP_B
// and logs the plan distance so you can compare it with the drawings.

using UnityEditor;
using UnityEngine;

public class SiteModelImporter : AssetPostprocessor
{
    const string Folder = "/Site Models/";

    bool IsSiteModel => assetPath.Replace('\\', '/').Contains(Folder);

    void OnPreprocessModel()
    {
        if (!IsSiteModel) return;
        var importer = assetImporter as ModelImporter;
        if (importer == null) return;  // e.g. .glb handled by glTFast
        importer.globalScale = 1f;
        importer.useFileScale = true;
        importer.bakeAxisConversion = true;
        importer.importCameras = false;
        importer.importLights = false;
        importer.importAnimation = false;
    }

    void OnPostprocessModel(GameObject root)
    {
        if (!IsSiteModel) return;
        Transform a = FindDeep(root.transform, "CP_A"), b = FindDeep(root.transform, "CP_B");
        if (a == null || b == null)
        {
            Debug.LogWarning($"{assetPath}: no CP_A / CP_B control points. SiteAligner can't place it. " +
                             "In Blender run examples/site_anchors.py, then export_ar.py.");
            return;
        }
        Vector3 d = b.position - a.position;
        float meters = new Vector2(d.x, d.z).magnitude, inches = meters * 39.3701f;
        Debug.Log($"{assetPath}: site model OK. CP_A -> CP_B = {meters:0.000} m " +
                  $"({Mathf.FloorToInt(inches / 12f)}' {inches % 12f:0.00}\"). Check this against the drawings.");
    }

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
}
