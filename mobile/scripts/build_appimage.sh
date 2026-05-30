#!/usr/bin/env bash
# Build a Linux AppImage from the Flutter desktop bundle.
# Requires `flutter` and `appimagetool` on PATH (override appimagetool via APPIMAGETOOL).
# Local use:  PATH="$HOME/flutter/bin:$PATH" mobile/scripts/build_appimage.sh
set -euo pipefail

MOBILE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$MOBILE_DIR"

APPIMAGETOOL="${APPIMAGETOOL:-appimagetool}"

flutter build linux --release

rm -rf .appdir dist
mkdir -p .appdir/usr/bin dist
cp -r build/linux/x64/release/bundle/* .appdir/usr/bin/
cp android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png .appdir/englishtutor.png

cat > .appdir/AppRun <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export LD_LIBRARY_PATH="${HERE}/usr/bin/lib:${LD_LIBRARY_PATH}"
cd "${HERE}/usr/bin" || exit 1
exec "${HERE}/usr/bin/englishbot" "$@"
EOF
chmod +x .appdir/AppRun

cat > .appdir/englishtutor.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=English Tutor
Comment=Personal English tutor powered by Claude
Exec=englishbot
Icon=englishtutor
Categories=Education;
Terminal=false
EOF

ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" .appdir dist/EnglishTutor-x86_64.AppImage
echo "Built: $MOBILE_DIR/dist/EnglishTutor-x86_64.AppImage"
