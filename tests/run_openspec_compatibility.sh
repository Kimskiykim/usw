#!/bin/sh

set -eu

MODE="${1:-pinned}"
case "$MODE" in
  pinned)
    VERSION=$(tr -d '[:space:]' < "$(dirname "$0")/openspec-version.txt")
    ;;
  latest)
    VERSION="latest"
    ;;
  *)
    echo "Usage: $0 pinned|latest" >&2
    exit 2
    ;;
esac

ISOLATED_DIR=$(mktemp -d)
trap 'rm -rf "$ISOLATED_DIR"' EXIT HUP INT TERM

echo "Installing real OpenSpec compatibility target: $VERSION"
npm install --prefix "$ISOLATED_DIR" --no-audit --no-fund "@fission-ai/openspec@$VERSION"

PATH="$ISOLATED_DIR/node_modules/.bin:$PATH"
export PATH
ACTUAL_VERSION=$(openspec --version)
if [ "$MODE" = "pinned" ] && [ "$ACTUAL_VERSION" != "$VERSION" ]; then
  echo "Expected OpenSpec $VERSION, got $ACTUAL_VERSION" >&2
  exit 1
fi
echo "Testing OpenSpec version: $ACTUAL_VERSION"
OPENSPEC_COMPAT_MODE="$MODE"
OPENSPEC_TESTED_VERSION="$ACTUAL_VERSION"
export OPENSPEC_COMPAT_MODE OPENSPEC_TESTED_VERSION

python3 -m unittest tests.test_openspec_compatibility tests.test_openspec_provider -v
