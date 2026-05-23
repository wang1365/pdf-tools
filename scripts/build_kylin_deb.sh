#!/usr/bin/env bash
set -euo pipefail

APP_NAME="pdf-tools"
ARCH="$(dpkg --print-architecture)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION="${VERSION:-$(sed -n 's/^version = "\(.*\)"/\1/p' "$ROOT/pyproject.toml" | head -n 1)}"
PKG_DIR="$ROOT/build/${APP_NAME}_${VERSION}_${ARCH}"
INSTALL_DIR="$PKG_DIR/opt/$APP_NAME"
PIP="pip3"
PYINSTALLER="pyinstaller"

if [[ -z "$VERSION" ]]; then
  echo "Could not read project version from pyproject.toml"
  exit 1
fi

rm -rf "$PKG_DIR" "$ROOT/build" "$ROOT/dist"

cd "$ROOT"


"$PIP" install pyinstaller

"$PYINSTALLER" \
  --onedir \
  -n pdf-tools-gui \
  --windowed \
  --clean \
  --noconfirm \
  --add-data "assets:assets" \
  --collect-all dearpygui \
  --collect-all PyMuPDF \
  --collect-all numpy \
  --collect-all lxml \
  pdf_tools/gui_main.py

mkdir -p "$INSTALL_DIR"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$PKG_DIR/DEBIAN"

cp -a "$ROOT/dist/pdf-tools-gui/." "$INSTALL_DIR/"
cp "$ROOT/assets/icon/app.png" "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/pdf-tools.png"

cat > "$PKG_DIR/usr/share/applications/pdf-tools.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=PDF Tools
Comment=PDF conversion and processing tools
Exec=/opt/pdf-tools/pdf-tools-gui
Icon=pdf-tools
Terminal=false
Categories=Office;Utility;
EOF

cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: pdf-tools
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: pdf-tools
Description: PDF Tools desktop application
EOF

find "$INSTALL_DIR" -type d -exec chmod 755 {} +
find "$INSTALL_DIR" -type f -exec chmod 644 {} +
chmod 755 "$INSTALL_DIR/pdf-tools-gui"
chmod 644 "$PKG_DIR/usr/share/applications/pdf-tools.desktop"
chmod 644 "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/pdf-tools.png"

dpkg-deb --build "$PKG_DIR"

echo "Built: $ROOT/build/${APP_NAME}_${VERSION}_${ARCH}.deb"
