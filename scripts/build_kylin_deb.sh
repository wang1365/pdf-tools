#!/usr/bin/env bash
set -euo pipefail

APP_NAME="pdf-tools"
ARCH="$(dpkg --print-architecture)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION="${VERSION:-$(sed -n 's/^version = "\(.*\)"/\1/p' "$ROOT/pyproject.toml" | head -n 1)}"
PKG_DIR="$ROOT/build/${APP_NAME}_${VERSION}_${ARCH}"
INSTALL_DIR="$PKG_DIR/opt/$APP_NAME"
PYTHON_BIN="${PYTHON_BIN:-python3.8}"
REQUIRED_GLIBCXX_VERSION="${REQUIRED_GLIBCXX_VERSION:-GLIBCXX_3.4.30}"

if [[ -z "$VERSION" ]]; then
  echo "Could not read project version from pyproject.toml"
  exit 1
fi

rm -rf "$PKG_DIR" "$ROOT/build" "$ROOT/dist"

cd "$ROOT"

command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
  echo "$PYTHON_BIN not found. Install Python 3.8.10 or set PYTHON_BIN=/path/to/python3.8"
  exit 1
}

"$PYTHON_BIN" -m pip install -e . pyinstaller

"$PYTHON_BIN" -m PyInstaller \
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

repair_libstdcxx() {
  local bundled_lib="$1"
  local candidate

  if strings "$bundled_lib" | grep -qx "$REQUIRED_GLIBCXX_VERSION"; then
    return
  fi

  echo "Bundled $bundled_lib does not provide $REQUIRED_GLIBCXX_VERSION"

  candidate="$(g++ -print-file-name=libstdc++.so.6 2>/dev/null || true)"
  if [[ -n "$candidate" && "$candidate" != "libstdc++.so.6" && -f "$candidate" ]] \
    && strings "$candidate" | grep -qx "$REQUIRED_GLIBCXX_VERSION"; then
    echo "Replacing bundled libstdc++.so.6 with $candidate"
    cp "$candidate" "$bundled_lib"
    return
  fi

  candidate="$(ldconfig -p 2>/dev/null | awk '/libstdc\+\+\.so\.6/{print $NF; exit}')"
  if [[ -n "$candidate" && -f "$candidate" ]] \
    && strings "$candidate" | grep -qx "$REQUIRED_GLIBCXX_VERSION"; then
    echo "Replacing bundled libstdc++.so.6 with $candidate"
    cp "$candidate" "$bundled_lib"
    return
  fi

  echo "Could not find libstdc++.so.6 with $REQUIRED_GLIBCXX_VERSION on the build machine."
  echo "Install a newer libstdc++/gcc runtime or build on the same Kylin image that can run Dear PyGui."
  exit 1
}

while IFS= read -r libstdcxx; do
  repair_libstdcxx "$libstdcxx"
done < <(find "$ROOT/dist/pdf-tools-gui" -type f -name "libstdc++.so.6")

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
