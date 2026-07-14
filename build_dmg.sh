#!/bin/bash
# Build a distributable .dmg for Browser Tab Counter.
#
#   ./build_dmg.sh
#
# Produces dist/BrowserTabCounter-<version>.dmg containing the .app plus an
# Applications shortcut for drag-to-install. The app is ad-hoc signed (required
# to run on Apple Silicon); it is NOT notarized, so first launch needs the
# right-click -> Open Gatekeeper step documented in the README.
set -euo pipefail
cd "$(dirname "$0")"

APP_NAME="Browser Tab Counter"
VERSION="0.1.0"
DMG_PATH="dist/BrowserTabCounter-${VERSION}.dmg"
PY="./.venv/bin/python"

echo "==> Cleaning previous build"
rm -rf build dist

echo "==> Building .app (py2app)"
"$PY" setup.py py2app >/dev/null

echo "==> Ad-hoc code signing (Apple Silicon requirement)"
codesign --force --deep --sign - "dist/${APP_NAME}.app"
codesign --verify --deep --strict "dist/${APP_NAME}.app" && echo "    signature OK"

echo "==> Staging DMG layout"
STAGE="dist/dmg-stage"
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -R "dist/${APP_NAME}.app" "$STAGE/"
ln -s /Applications "$STAGE/Applications"

echo "==> Creating DMG"
rm -f "$DMG_PATH"
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$STAGE" \
    -ov -format UDZO \
    "$DMG_PATH" >/dev/null

rm -rf "$STAGE"
echo "==> Done: ${DMG_PATH}"
ls -lh "$DMG_PATH"
