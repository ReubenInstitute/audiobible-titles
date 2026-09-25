#!/bin/sh
# Build audiobible-titles_<version>_all.deb
# Usage: packaging/deb/build.sh
set -eu

cd "$(dirname "$0")/../.."
REPO_ROOT="$(pwd)"
VERSION="0.$(git rev-list --count HEAD)"
sed -i "s/^Version: .*/Version: $VERSION/" packaging/deb/control

PKG_DIR="$REPO_ROOT/debian-pkg"
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN" "$PKG_DIR/var/lib/audiobible/titles"
cp packaging/deb/control "$PKG_DIR/DEBIAN/control"
cp *.mp3 *.csv "$PKG_DIR/var/lib/audiobible/titles/"
dpkg-deb --build --root-owner-group "$PKG_DIR" "audiobible-titles_${VERSION}_all.deb"
rm -rf "$PKG_DIR"
echo "Built audiobible-titles_${VERSION}_all.deb"
