#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/apps/mobile"
if ! command -v flutter >/dev/null; then
  echo 'Install Flutter 3.50+ (Dart >= 3.6) first: https://docs.flutter.dev/get-started/install' >&2
  exit 1
fi
# Generates missing platform runners; existing lib/ and test/ content are retained.
flutter create --project-name optilexis_mobile --platforms=android,ios --org ai.optilexis .
# Permit cleartext loopback API only in Android DEBUG builds.
mkdir -p android/app/src/debug
cat > android/app/src/debug/AndroidManifest.xml <<'XML'
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <application android:usesCleartextTraffic="true" />
</manifest>
XML
# Generate native login callback and permission settings.
python3 "$ROOT/scripts/configure_native.py"
# iOS ATS local debug rule may require developer-specific Xcode simulator configuration.
flutter pub get
flutter analyze
flutter test
printf '\nFlutter checked. For the simulator, authenticate through the debug-only token screen.\n'
