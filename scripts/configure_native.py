#!/usr/bin/env python3
"""Apply repeatable Android and iOS native settings to generated Flutter runners."""
from pathlib import Path
import plistlib

ROOT = Path(__file__).resolve().parents[1] / "apps" / "mobile"
SCHEME = "ai.optilexis"

def android() -> None:
    gradle = ROOT / "android/app/build.gradle.kts"
    source = gradle.read_text()
    if '"appAuthRedirectScheme"' not in source:
        source = source.replace("    defaultConfig {",
            '    defaultConfig {\n        manifestPlaceholders.putAll(mapOf("appAuthRedirectScheme" to "ai.optilexis"))', 1)
    source = source.replace("minSdk = flutter.minSdkVersion", "minSdk = 24")
    gradle.write_text(source)

    manifest = ROOT / "android/app/src/main/AndroidManifest.xml"
    content = manifest.read_text()
    for permission in ("android.permission.INTERNET",
                       "android.permission.ACCESS_COARSE_LOCATION",
                       "android.permission.ACCESS_FINE_LOCATION"):
        if permission not in content:
            pos = content.find(">")
            if pos < 0:
                raise RuntimeError("Invalid Android manifest")
            content = (content[:pos + 1] +
                       '\n    <uses-permission android:name="' + permission + '" />' +
                       content[pos + 1:])
    manifest.write_text(content)

def ios() -> None:
    plist = ROOT / "ios/Runner/Info.plist"
    with plist.open("rb") as file:
        settings = plistlib.load(file)
    settings["NSLocationWhenInUseUsageDescription"] = (
        "Optilexis uses your location only when you explicitly request a position check. "
        "It does not continuously track or upload your location.")
    urls = settings.setdefault("CFBundleURLTypes", [])
    if not any(SCHEME in item.get("CFBundleURLSchemes", []) for item in urls):
        urls.append({"CFBundleTypeRole": "Editor", "CFBundleURLSchemes": [SCHEME]})
    with plist.open("wb") as file:
        plistlib.dump(settings, file, sort_keys=False)

if __name__ == "__main__":
    android()
    ios()
    print("Configured callback scheme and foreground location permissions.")
