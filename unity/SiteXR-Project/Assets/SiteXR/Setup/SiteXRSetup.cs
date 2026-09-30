// First-open step 2 of 2: build the AR scene and configure iOS.
// Runs automatically once AR Foundation is installed and Assets/Scenes/Site.unity
// doesn't exist yet. Re-run any time from menu SiteXR > Set Up AR Scene.

using System;
using System.IO;
using System.Linq;
using System.Reflection;
using Unity.XR.CoreUtils;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

[InitializeOnLoad]
static class SiteXRSetup
{
    const string ScenePath = "Assets/Scenes/Site.unity";
    const string ModelPath = "Assets/Site Models/stud_wall.fbx";
    const string TriedKey = "SiteXR.SetupTried";

    static SiteXRSetup()
    {
        if (File.Exists(ScenePath) || SessionState.GetBool(TriedKey, false)) return;
        SessionState.SetBool(TriedKey, true);
        EditorApplication.delayCall += RunWhenIdle;
    }

    static void RunWhenIdle()
    {
        if (EditorApplication.isCompiling || EditorApplication.isUpdating)
        {
            EditorApplication.delayCall += RunWhenIdle;
            return;
        }
        Run();
    }

    [MenuItem("SiteXR/Set Up AR Scene")]
    static void Run()
    {
        if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        ConfigurePlayer();
        bool arkit = EnableARKit();
        bool scene = BuildScene();
        bool ios = SwitchToIOS();

        Debug.Log("SiteXR setup:\n" +
                  $"  scene {(scene ? "OK" : "FAILED, see errors above")}: {ScenePath}\n" +
                  $"  ARKit {(arkit ? "enabled" : "NOT enabled: tick ARKit on the iOS tab of Project Settings > XR Plug-in Management")}\n" +
                  $"  iOS build target {(ios ? "active" : "not active: install iOS Build Support in Unity Hub, then File > Build Profiles/Settings > iOS > Switch Platform")}\n" +
                  "  Next: File > Build And Run (iOS), then run from Xcode on your iPad/iPhone.");
    }

    static void ConfigurePlayer()
    {
        PlayerSettings.productName = "SiteXR";
        PlayerSettings.iOS.cameraUsageDescription = "The camera shows your model on site in AR.";
        if (!Version.TryParse(PlayerSettings.iOS.targetOSVersionString, out Version v) || v < new Version(15, 0))
            PlayerSettings.iOS.targetOSVersionString = "15.0";  // current ARKit plug-ins need iOS 15+
        string id = PlayerSettings.GetApplicationIdentifier(NamedBuildTarget.iOS);
        if (string.IsNullOrEmpty(id) || id.Contains("DefaultCompany"))
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.iOS, "com.cristyandavid.sitexr");
    }

    static bool BuildScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        var light = new GameObject("Directional Light").AddComponent<Light>();
        light.type = LightType.Directional;
        light.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

        if (UnityEngine.Object.FindFirstObjectByType<ARSession>() == null)
            new GameObject("AR Session", typeof(ARSession), typeof(ARInputManager));

        // Use AR Foundation's own menu so the camera + tracking setup matches your package version.
        string[] originMenus = { "GameObject/XR/XR Origin (Mobile AR)", "GameObject/XR/XR Origin (AR)", "GameObject/XR/AR Session Origin" };
        foreach (string menu in originMenus)
            if (UnityEngine.Object.FindFirstObjectByType<XROrigin>() == null)
                EditorApplication.ExecuteMenuItem(menu);
        var origin = UnityEngine.Object.FindFirstObjectByType<XROrigin>();
        if (origin == null)
        {
            Debug.LogError("SiteXR: couldn't create the XR Origin. Add it by hand: GameObject > XR > XR Origin (Mobile AR), then run SiteXR > Set Up AR Scene again.");
            return false;
        }
        origin.transform.SetParent(null);
        origin.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);

        var planes = GetOrAdd<ARPlaneManager>(origin.gameObject);
        planes.requestedDetectionMode = PlaneDetectionMode.Horizontal;
        var raycasts = GetOrAdd<ARRaycastManager>(origin.gameObject);
        var anchors = GetOrAdd<ARAnchorManager>(origin.gameObject);

        var aligner = new GameObject("Site Aligner").AddComponent<SiteAligner>();
        aligner.raycastManager = raycasts;
        aligner.anchorManager = anchors;
        aligner.modelPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
        if (aligner.modelPrefab == null)
            Debug.LogWarning($"SiteXR: {ModelPath} not found. Drag your model into Site Aligner > Model Prefab.");

        Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
        if (!EditorSceneManager.SaveScene(scene, ScenePath)) return false;
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
        return true;
    }

    static bool SwitchToIOS()
    {
        if (EditorUserBuildSettings.activeBuildTarget == BuildTarget.iOS) return true;
        if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.iOS, BuildTarget.iOS)) return false;
        return EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.iOS, BuildTarget.iOS);
    }

    static T GetOrAdd<T>(GameObject go) where T : Component
    {
        T existing = go.GetComponent<T>();  // no ??: the Editor can return a "fake null" object
        return existing != null ? existing : go.AddComponent<T>();
    }

    // Ticks ARKit in XR Plug-in Management (iOS). Done by reflection so an API
    // difference between XR Management versions can't stop the project compiling;
    // on any failure it opens the settings page so you can tick it by hand.
    static bool EnableARKit()
    {
        const string loader = "UnityEngine.XR.ARKit.ARKitLoader";
        try
        {
            Type generalType = Type.GetType("UnityEngine.XR.Management.XRGeneralSettings, Unity.XR.Management", true);
            Type perTargetType = Type.GetType("UnityEditor.XR.Management.XRGeneralSettingsPerBuildTarget, Unity.XR.Management.Editor", true);
            Type storeType = Type.GetType("UnityEditor.XR.Management.Metadata.XRPackageMetadataStore, Unity.XR.Management.Editor", true);
            string key = (string)generalType.GetField("k_SettingsKey").GetRawConstantValue();

            EditorBuildSettings.TryGetConfigObject(key, out UnityEngine.Object perTarget);
            if (perTarget == null)
            {
                perTarget = ScriptableObject.CreateInstance(perTargetType);
                Directory.CreateDirectory("Assets/XR");
                AssetDatabase.CreateAsset(perTarget, "Assets/XR/XRGeneralSettingsPerBuildTarget.asset");
                EditorBuildSettings.AddConfigObject(key, perTarget, true);
            }
            if (!(bool)Call(perTarget, "HasManagerSettingsForBuildTarget", BuildTargetGroup.iOS))
                Call(perTarget, "CreateDefaultManagerSettingsForBuildTarget", BuildTargetGroup.iOS);
            object general = Call(perTarget, "SettingsForBuildTarget", BuildTargetGroup.iOS);
            object manager = (generalType.GetProperty("AssignedSettings") ?? generalType.GetProperty("Manager")).GetValue(general);

            var assign = storeType.GetMethods(BindingFlags.Public | BindingFlags.Static)
                .First(m => m.Name == "AssignLoader" && m.GetParameters().Length == 3);
            assign.Invoke(null, new[] { manager, loader, (object)BuildTargetGroup.iOS });
            AssetDatabase.SaveAssets();

            var loaders = manager.GetType().GetProperty("activeLoaders")?.GetValue(manager) as System.Collections.IEnumerable;
            return loaders == null || loaders.Cast<object>().Any(l => l.GetType().FullName == loader);
        }
        catch (Exception e)
        {
            Debug.LogWarning("SiteXR: couldn't enable ARKit automatically (" + (e.InnerException ?? e).Message +
                             "). Tick ARKit on the iOS tab of the settings page that just opened.");
            SettingsService.OpenProjectSettings("Project/XR Plug-in Management");
            return false;
        }
    }

    static object Call(object target, string method, params object[] args)
    {
        MethodInfo m = target.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .First(x => x.Name == method && x.GetParameters().Length == args.Length);
        return m.Invoke(target, args);
    }
}
