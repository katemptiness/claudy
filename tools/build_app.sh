#!/bin/bash
# Build Claudy.app and install it into /Applications, replacing what is there.
#
#   tools/build_app.sh              build, install, relaunch
#   tools/build_app.sh --no-launch  build and install, leave Claudy closed
#
# A symlink from /Applications into dist/ would look simpler, but py2app
# deletes and recreates the bundle on every build, and the Login Items entry
# remembers the app it was given — so autostart would quietly break. Copying a
# real bundle to a fixed path keeps that entry, and the icon, working.
#
# The build directories are removed afterwards: Spotlight indexes any .app it
# finds, and a leftover dist/Claudy.app shows up as a second, confusing hit.

set -euo pipefail
cd "$(dirname "$0")/.."

TARGET="/Applications/Claudy.app"
LOG=/tmp/claudy-build.log

echo "==> Building"
rm -rf build dist
python3 setup.py py2app >"$LOG" 2>&1 || {
    echo "Build failed; see $LOG" >&2
    tail -20 "$LOG" >&2
    exit 1
}

if [ -e "$TARGET" ] && [ ! -x "$TARGET/Contents/MacOS/Claudy" ]; then
    echo "$TARGET exists but is not a Claudy bundle; leaving it alone" >&2
    exit 1
fi

if pgrep -f "$TARGET/Contents/MacOS/Claudy" >/dev/null; then
    echo "==> Quitting the running Claudy"
    osascript -e 'tell application "Claudy" to quit' 2>/dev/null || true
    sleep 2
    pkill -f "$TARGET/Contents/MacOS/Claudy" 2>/dev/null || true
fi

echo "==> Installing to $TARGET"
rm -rf "$TARGET"
ditto dist/Claudy.app "$TARGET"
rm -rf build dist
# Let Launch Services pick up the new build (icon, version, registration)
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
    -f "$TARGET" 2>/dev/null || true

if [ "${1:-}" != "--no-launch" ]; then
    echo "==> Launching"
    open -a Claudy
fi
echo "Done: $TARGET"
