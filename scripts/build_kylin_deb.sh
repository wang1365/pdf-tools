#!/usr/bin/env bash
set -euo pipefail

APP_NAME="pdf-tools"
VERSION="0.1.0"
ARCH="$(dpkg --print-architecture)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PKG_DIR="$ROOT/build/${APP_NAME}_${VERSION}_${ARCH}"
INSTALL_DIR="$PKG_DIR/opt/$APP_NAME"
VENV_DIR="$ROOT/.venv"
PIP="$VENV_DIR/bin/pip3"
PYINSTALLER="$VENV_DIR/bin/pyinstaller"

command -v python3 >/dev/null 2>&1 || {
  echo "python3 not found. Install python3 first."
  exit 1
}

command -v pip3 >/dev/null 2>&1 || {
  echo "pip3 not found. Install python3-pip first."
  exit 1
}

rm -rf "$PKG_DIR" "$ROOT/build" "$ROOT/dist"

cd "$ROOT"

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$PIP" install --upgrade pip
"$PIP" install -e "$ROOT" pyinstaller

"$PYINSTALLER" \
  -F \
  -n pdf-tools-gui \
  --windowed \
  --clean \
  --noconfirm \
  --add-data "assets:assets" \
  --collect-all PySide6 \
  --collect-all PyMuPDF \
  --collect-all numpy \
  --collect-all lxml \
  pdf_tools/gui_main.py

mkdir -p "$INSTALL_DIR"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$PKG_DIR/DEBIAN"

cp "$ROOT/dist/pdf-tools-gui" "$INSTALL_DIR/pdf-tools-gui"
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

chmod 755 "$INSTALL_DIR/pdf-tools-gui"
chmod 644 "$PKG_DIR/usr/share/applications/pdf-tools.desktop"
chmod 644 "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/pdf-tools.png"

dpkg-deb --build "$PKG_DIR"

echo "Built: $ROOT/build/${APP_NAME}_${VERSION}_${ARCH}.deb"
