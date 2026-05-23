#!/usr/bin/env bash
set -euo pipefail

APP_NAME="pdf-tools"
PACKAGE_NAME="${PACKAGE_NAME:-pdf-tools-lite}"
VERSION="${VERSION:-0.1.0}"
PYTHON_BIN="${PYTHON_BIN:-python3.8}"
ARCH="$(dpkg --print-architecture)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PKG_DIR="$ROOT/build/${PACKAGE_NAME}_${VERSION}_${ARCH}"
APP_DIR="$PKG_DIR/opt/$APP_NAME"

command -v dpkg-deb >/dev/null 2>&1 || {
  echo "dpkg-deb not found. Install dpkg-dev first."
  exit 1
}

command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
  echo "$PYTHON_BIN not found. Set PYTHON_BIN=/path/to/python if needed."
  exit 1
}

cd "$ROOT"

"$PYTHON_BIN" - <<'PY'
import sys

if sys.version_info < (3, 8):
    raise SystemExit("Python 3.8 or newer is required")
PY

if [[ "${SKIP_PYTHON_COMPILE_CHECK:-0}" != "1" ]]; then
  "$PYTHON_BIN" -m compileall -q "$ROOT/pdf_tools" || {
    echo
    echo "Source is not compatible with $PYTHON_BIN."
    echo "Current project metadata requires Python >=3.10; set PYTHON_BIN=python3.10 or update the source for Python 3.8."
    echo "Set SKIP_PYTHON_COMPILE_CHECK=1 only if you intentionally want to build without this check."
    exit 1
  }
fi

rm -rf "$PKG_DIR" "$ROOT/build/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
mkdir -p \
  "$APP_DIR" \
  "$PKG_DIR/usr/bin" \
  "$PKG_DIR/usr/share/applications" \
  "$PKG_DIR/usr/share/icons/hicolor/256x256/apps" \
  "$PKG_DIR/DEBIAN"

cp -R "$ROOT/pdf_tools" "$APP_DIR/pdf_tools"
cp -R "$ROOT/assets" "$APP_DIR/assets"
cp "$ROOT/requirements.txt" "$APP_DIR/requirements.txt"
find "$APP_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$APP_DIR" -type f -name "*.pyc" -delete

cat > "$PKG_DIR/usr/bin/pdf-tools-gui" <<EOF
#!/usr/bin/env bash
set -e
APP_DIR="/opt/$APP_NAME"
VENV_DIR="\$APP_DIR/.venv"
if [[ ! -x "\$VENV_DIR/bin/python" ]]; then
  echo "Runtime environment is missing: \$VENV_DIR"
  echo "Reinstall the package or run: sudo dpkg-reconfigure $PACKAGE_NAME"
  exit 1
fi
export PYTHONPATH="\$APP_DIR"
exec "\$VENV_DIR/bin/python" -m pdf_tools.gui_main "\$@"
EOF

cat > "$PKG_DIR/usr/bin/pdf-tools" <<EOF
#!/usr/bin/env bash
set -e
APP_DIR="/opt/$APP_NAME"
VENV_DIR="\$APP_DIR/.venv"
if [[ ! -x "\$VENV_DIR/bin/python" ]]; then
  echo "Runtime environment is missing: \$VENV_DIR"
  echo "Reinstall the package or run: sudo dpkg-reconfigure $PACKAGE_NAME"
  exit 1
fi
export PYTHONPATH="\$APP_DIR"
exec "\$VENV_DIR/bin/python" -m pdf_tools "\$@"
EOF

cat > "$PKG_DIR/usr/share/applications/pdf-tools.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=PDF Tools
Comment=PDF conversion and processing tools
Exec=/usr/bin/pdf-tools-gui
Icon=pdf-tools
Terminal=false
Categories=Office;Utility;
EOF

cp "$ROOT/assets/icon/app.png" "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/pdf-tools.png"

cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: pdf-tools
Depends: python3.8, python3.8-venv, python3-pip
Description: PDF Tools desktop application (lite source package)
 This package installs PDF Tools source files and creates a local virtual
 environment on the target machine instead of bundling a PyInstaller binary.
EOF

cat > "$PKG_DIR/DEBIAN/postinst" <<EOF
#!/usr/bin/env bash
set -e

APP_DIR="/opt/$APP_NAME"
VENV_DIR="\$APP_DIR/.venv"
PYTHON_BIN="$PYTHON_BIN"

if ! command -v "\$PYTHON_BIN" >/dev/null 2>&1; then
  echo "\$PYTHON_BIN not found"
  exit 1
fi

"\$PYTHON_BIN" -m venv "\$VENV_DIR"
"\$VENV_DIR/bin/python" -m pip install --upgrade pip
"\$VENV_DIR/bin/python" -m pip install -r "\$APP_DIR/requirements.txt"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi
EOF

cat > "$PKG_DIR/DEBIAN/postrm" <<EOF
#!/usr/bin/env bash
set -e

if [[ "\${1:-}" = "remove" || "\${1:-}" = "purge" ]]; then
  rm -rf "/opt/$APP_NAME/.venv"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi
EOF

chmod 755 \
  "$PKG_DIR/usr/bin/pdf-tools" \
  "$PKG_DIR/usr/bin/pdf-tools-gui" \
  "$PKG_DIR/DEBIAN/postinst" \
  "$PKG_DIR/DEBIAN/postrm"
chmod 644 \
  "$PKG_DIR/usr/share/applications/pdf-tools.desktop" \
  "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/pdf-tools.png"

dpkg-deb --build "$PKG_DIR"

echo "Built: $ROOT/build/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
