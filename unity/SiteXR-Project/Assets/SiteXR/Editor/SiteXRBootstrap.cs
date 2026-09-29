// First-open step 1 of 2: install the AR packages.
//
// Package versions aren't pinned in Packages/manifest.json. On first open this
// asks the Package Manager for the newest AR Foundation + ARKit that match
// your Unity version. The SiteXR runtime/setup code only compiles once AR
// Foundation is present (see the asmdefs), so the project never opens with
// errors. Step 2 is Setup/SiteXRSetup.cs.

using System;
using UnityEditor;
using UnityEditor.PackageManager;
using UnityEditor.PackageManager.Requests;
using UnityEngine;

[InitializeOnLoad]
static class SiteXRBootstrap
{
    static readonly string[] Packages = { "com.unity.xr.arfoundation", "com.unity.xr.arkit" };
    const string TriedKey = "SiteXR.PackagesRequested";

    static AddAndRemoveRequest request;

    static SiteXRBootstrap()
    {
        if (ARFoundationInstalled() || SessionState.GetBool(TriedKey, false)) return;
        SessionState.SetBool(TriedKey, true);
        EditorApplication.delayCall += Install;
    }

    [MenuItem("SiteXR/Install AR Packages")]
    static void Install()
    {
        Debug.Log("SiteXR: installing AR Foundation + ARKit (a few minutes on first open)...");
        request = Client.AddAndRemove(Packages, null);
        EditorApplication.update += Poll;
    }

    static void Poll()
    {
        if (!request.IsCompleted) return;
        EditorApplication.update -= Poll;
        if (request.Status == StatusCode.Success)
            Debug.Log("SiteXR: AR packages installed. Building the AR scene next...");
        else
            Debug.LogError("SiteXR: package install failed: " + request.Error?.message +
                           "\nCheck your internet connection, then use menu SiteXR > Install AR Packages.");
    }

    static bool ARFoundationInstalled() =>
        Type.GetType("UnityEngine.XR.ARFoundation.ARSession, Unity.XR.ARFoundation") != null;
}
