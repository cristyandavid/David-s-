#!/usr/bin/env python3
"""Generate one unsigned .shortcut per service. Sign on a Mac with sign.sh."""
import plistlib, uuid, pathlib

SERVICES = {  # name: (icon color, glyph)
    "Garbage": (4282601983, 59780), "Coffee Mug": (4292093695, 59781),
    "Coffee Machine": (4292093695, 59781), "Laundry": (431817727, 59780),
    "Toothbrush": (4282601983, 59780),
}

def tok(s):
    return {"Value": {"string": s, "attachmentsByRange": {}}, "WFSerializationType": "WFTextTokenString"}

def build(service, color, glyph):
    post_uuid = str(uuid.uuid4()).upper()
    item = lambda k, v: {"WFItemType": 0, "WFKey": tok(k), "WFValue": tok(v)}
    post = {
        "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
        "WFWorkflowActionParameters": {
            "UUID": post_uuid,
            "WFURL": "https://script.google.com/macros/s/PASTE_ID/exec?token=PASTE_TOKEN",
            "WFHTTPMethod": "POST",
            "WFHTTPBodyType": "JSON",
            "WFJSONValues": {"Value": {"WFDictionaryFieldValueItems": [
                item("service", service), item("source", "NFC")]},
                "WFSerializationType": "WFDictionaryFieldValue"},
        },
    }
    note = {
        "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
        "WFWorkflowActionParameters": {
            "WFNotificationActionTitle": service,
            "WFNotificationActionBody": {"Value": {"string": "￼", "attachmentsByRange": {
                "{0, 1}": {"OutputUUID": post_uuid, "Type": "ActionOutput",
                           "OutputName": "Contents of URL"}}},
                "WFSerializationType": "WFTextTokenString"},
        },
    }
    return {
        "WFWorkflowClientVersion": "1300.0.1",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientRelease": 900,
        "WFWorkflowIcon": {"WFWorkflowIconStartColor": color, "WFWorkflowIconGlyphNumber": glyph},
        "WFWorkflowTypes": [],
        "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowImportQuestions": [{
            "ParameterKey": "WFURL", "Category": "Parameter", "ActionIndex": 0,
            "Text": "Paste your Apps Script web app URL (with ?token=...)",
            "DefaultValue": post["WFWorkflowActionParameters"]["WFURL"]}],
        "WFWorkflowActions": [post, note],
    }

out = pathlib.Path(__file__).parent / "shortcuts"
out.mkdir(exist_ok=True)
for name, (color, glyph) in SERVICES.items():
    with open(out / f"Log {name}.shortcut", "wb") as f:
        plistlib.dump(build(name, color, glyph), f, fmt=plistlib.FMT_XML)
    print("wrote", f"Log {name}.shortcut")
