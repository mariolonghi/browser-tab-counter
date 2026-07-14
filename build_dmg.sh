#!/bin/bash
# Build a distributable .dmg for Browser Tab Counter.
#
#   ./build_dmg.sh
#
# Signing behaviour is automatic:
#   * If a "Developer ID Application" certificate is in your keychain (paid
#     Apple Developer Program), the app is signed with it + the hardened runtime
#     + entitlements.plist  ->  eligible for notarization.
#   * Otherwise it falls back to an ad-hoc signature (runs on Apple Silicon, but
#     users need the one-time right-click -> Open).
#
# Notarization (optional, needs the Developer ID signature above) runs when you
# provide notarytool credentials, either:
#   NOTARY_PROFILE=<name>                       # from `notarytool store-credentials`
# or:
#   NOTARY_APPLE_ID=... NOTARY_TEAM_ID=... NOTARY_PASSWORD=<app-specific-pw>
#
# Override the signing identity explicitly with:  SIGN_IDENTITY="Developer ID Application: ..."
set -euo pipefail
cd "$(dirname "$0")"

APP_NAME="Browser Tab Counter"
VERSION="$(./.venv/bin/python -c 'import appinfo; print(appinfo.VERSION)')"
DMG_PATH="dist/BrowserTabCounter-${VERSION}.dmg"
PY="./.venv/bin/python"
APP="dist/${APP_NAME}.app"

echo "==> Cleaning previous build"
rm -rf build dist

echo "==> Building .app (py2app) — version ${VERSION}"
"$PY" setup.py py2app >/dev/null

# ----------------------------------------------------------------------------
# Sign
# ----------------------------------------------------------------------------
IDENTITY="${SIGN_IDENTITY:-}"
if [[ -z "$IDENTITY" ]]; then
    # Auto-detect a Developer ID Application identity.
    IDENTITY="$(security find-identity -v -p codesigning \
        | grep -o '"Developer ID Application:.*"' | head -1 | tr -d '"' || true)"
fi

if [[ -n "$IDENTITY" ]]; then
    echo "==> Signing with Developer ID + hardened runtime:"
    echo "    $IDENTITY"
    codesign --force --deep --timestamp \
        --options runtime \
        --entitlements entitlements.plist \
        --sign "$IDENTITY" "$APP"
    NOTARIZABLE=1
else
    echo "==> No Developer ID cert found — ad-hoc signing (not notarizable)"
    codesign --force --deep --sign - "$APP"
    NOTARIZABLE=0
fi
codesign --verify --deep --strict "$APP" && echo "    signature OK"

# ----------------------------------------------------------------------------
# Package DMG
# ----------------------------------------------------------------------------
echo "==> Staging DMG layout"
STAGE="dist/dmg-stage"
rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"

echo "==> Creating DMG"
rm -f "$DMG_PATH"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE" -ov -format UDZO "$DMG_PATH" >/dev/null
rm -rf "$STAGE"

# ----------------------------------------------------------------------------
# Notarize + staple (optional)
# ----------------------------------------------------------------------------
notarize=0
if [[ "$NOTARIZABLE" == "1" ]]; then
    if [[ -n "${NOTARY_PROFILE:-}" ]]; then
        NOTARY_ARGS=(--keychain-profile "$NOTARY_PROFILE"); notarize=1
    elif [[ -n "${NOTARY_APPLE_ID:-}" && -n "${NOTARY_TEAM_ID:-}" && -n "${NOTARY_PASSWORD:-}" ]]; then
        NOTARY_ARGS=(--apple-id "$NOTARY_APPLE_ID" --team-id "$NOTARY_TEAM_ID" --password "$NOTARY_PASSWORD"); notarize=1
    fi
fi

if [[ "$notarize" == "1" ]]; then
    if ! xcrun --find notarytool >/dev/null 2>&1; then
        echo "==> WARNING: notarytool not found (install Xcode). Skipping notarization."
    else
        echo "==> Notarizing (this can take a few minutes)…"
        xcrun notarytool submit "$DMG_PATH" "${NOTARY_ARGS[@]}" --wait
        echo "==> Stapling ticket to the DMG"
        xcrun stapler staple "$DMG_PATH"
        xcrun stapler validate "$DMG_PATH" && echo "    staple OK"
    fi
else
    echo "==> Notarization skipped (no credentials, or ad-hoc build)."
fi

echo "==> Done: ${DMG_PATH}"
ls -lh "$DMG_PATH"
