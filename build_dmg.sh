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
# Resolve notary credentials (if any)
# ----------------------------------------------------------------------------
NOTARY_ARGS=()
HAVE_NOTARY=0
if [[ "$NOTARIZABLE" == "1" ]]; then
    if [[ -n "${NOTARY_PROFILE:-}" ]]; then
        NOTARY_ARGS=(--keychain-profile "$NOTARY_PROFILE"); HAVE_NOTARY=1
    elif [[ -n "${NOTARY_APPLE_ID:-}" && -n "${NOTARY_TEAM_ID:-}" && -n "${NOTARY_PASSWORD:-}" ]]; then
        NOTARY_ARGS=(--apple-id "$NOTARY_APPLE_ID" --team-id "$NOTARY_TEAM_ID" --password "$NOTARY_PASSWORD")
        HAVE_NOTARY=1
    fi
    if [[ "$HAVE_NOTARY" == "1" ]] && ! xcrun --find notarytool >/dev/null 2>&1; then
        echo "==> WARNING: notarytool not found (install full Xcode). Skipping notarization."
        HAVE_NOTARY=0
    fi
fi

# ----------------------------------------------------------------------------
# Notarize + staple the APP itself (so the ticket travels with it — works even
# on a first launch while offline). notarytool takes a zip, not a bare .app.
# ----------------------------------------------------------------------------
if [[ "$HAVE_NOTARY" == "1" ]]; then
    echo "==> Notarizing the app (this can take a few minutes)…"
    ZIP="dist/${APP_NAME}.zip"
    ditto -c -k --keepParent "$APP" "$ZIP"
    SUBMIT_OUT="$(xcrun notarytool submit "$ZIP" "${NOTARY_ARGS[@]}" --wait 2>&1)" || true
    echo "$SUBMIT_OUT"
    rm -f "$ZIP"
    SUBMISSION_ID="$(printf '%s\n' "$SUBMIT_OUT" | awk '/id:/{print $2; exit}')"
    if printf '%s\n' "$SUBMIT_OUT" | grep -q "status: Accepted"; then
        echo "==> Stapling ticket to the app"
        xcrun stapler staple "$APP"
        xcrun stapler validate "$APP" && echo "    app staple OK"
    else
        echo "==> NOTARIZATION FAILED — fetching the detailed issue log:"
        [[ -n "$SUBMISSION_ID" ]] && xcrun notarytool log "$SUBMISSION_ID" "${NOTARY_ARGS[@]}" || true
        exit 1
    fi
fi

# ----------------------------------------------------------------------------
# Package DMG (from the now-stapled app)
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

if [[ "$HAVE_NOTARY" == "1" ]]; then
    echo "==> Stapling the DMG too"
    xcrun stapler staple "$DMG_PATH" && echo "    dmg staple OK" || echo "    (dmg staple skipped)"
elif [[ "$NOTARIZABLE" == "1" ]]; then
    echo "==> NOTE: signed with Developer ID but NOT notarized (no notary creds)."
else
    echo "==> NOTE: ad-hoc build — users need right-click -> Open on first launch."
fi

echo "==> Done: ${DMG_PATH}"
ls -lh "$DMG_PATH"
