#!/usr/bin/env bash
set -euo pipefail
# Executed on a development workstation with Flutter installed.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/apps/mobile"
if ! command -v flutter >/dev/null; then
  echo 'Install Flutter 3.27+ (Dart >= 3.6) first: https://docs.flutter.dev/get-started/install' >&2
  exit 1
fi
flutter create --project-name optilexis_mobile --platforms=android,ios --org ai.optilexis .
# Allow local HTTP API only in Android DEBUG builds.
mkdir -p android/app/src/debug
cat > android/app/src/debug/AndroidManifest.xml <<'XML'
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <application android:usesCleartextTraffic="true" />
</manifest>
XML
# iOS local-network ATS exceptions may need Xcode development settings, depending on host URL.
flutter pub get
flutter analyze
flutter test
printf '\nFlutter native runners generated. Set local API URL using --dart-define.\n'
