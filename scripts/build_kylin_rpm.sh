#!/usr/bin/env bash
set -euo pipefail

APP_NAME="pdf-tools"
RELEASE="${RELEASE:-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION="${VERSION:-$(sed -n 's/^version = "\(.*\)"/\1/p' "$ROOT/pyproject.toml" | head -n 1)}"
RPM_TOP="$ROOT/build/rpmbuild"
SPEC_FILE="$RPM_TOP/SPECS/${APP_NAME}.spec"
DIST_DIR="$ROOT/dist"

if [[ -z "$VERSION" ]]; then
  echo "Could not read project version from pyproject.toml"
  exit 1
fi

command -v rpmbuild >/dev/null 2>&1 || {
  echo "rpmbuild not found. Install it first: yum install -y rpm-build"
  exit 1
}

command -v uv >/dev/null 2>&1 || {
  echo "uv not found. Install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
}

cd "$ROOT"
rm -rf "$DIST_DIR" "$RPM_TOP"
mkdir -p \
  "$RPM_TOP/BUILD" \
  "$RPM_TOP/BUILDROOT" \
  "$RPM_TOP/RPMS" \
  "$RPM_TOP/SOURCES" \
  "$RPM_TOP/SPECS" \
  "$RPM_TOP/SRPMS"

if [[ ! -d "$ROOT/.venv" ]]; then
  uv venv --python python3
fi

uv sync
uv pip install pyinstaller

uv run pyinstaller \
  -F \
  -n pdf-tools \
  --clean \
  --noconfirm \
  --collect-all PyMuPDF \
  --collect-all numpy \
  --collect-all lxml \
  pdf_tools/__main__.py

uv run pyinstaller \
  -F \
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

test -x "$DIST_DIR/pdf-tools"
test -x "$DIST_DIR/pdf-tools-gui"
test -f "$ROOT/assets/icon/app.png"

cat > "$SPEC_FILE" <<EOF
Name:           $APP_NAME
Version:        $VERSION
Release:        $RELEASE%{?dist}
Summary:        PDF Tools desktop application
License:        Proprietary

%description
PDF conversion and processing tools with CLI and Dear PyGui desktop entry points.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/pdf-tools
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps

cp "$DIST_DIR/pdf-tools" %{buildroot}/opt/pdf-tools/pdf-tools
cp "$DIST_DIR/pdf-tools-gui" %{buildroot}/opt/pdf-tools/pdf-tools-gui
cp "$ROOT/assets/icon/app.png" %{buildroot}/usr/share/icons/hicolor/256x256/apps/pdf-tools.png

ln -s /opt/pdf-tools/pdf-tools %{buildroot}/usr/bin/pdf-tools
ln -s /opt/pdf-tools/pdf-tools-gui %{buildroot}/usr/bin/pdf-tools-gui

cat > %{buildroot}/usr/share/applications/pdf-tools.desktop <<DESKTOP
[Desktop Entry]
Type=Application
Name=PDF Tools
Comment=PDF conversion and processing tools
Exec=/opt/pdf-tools/pdf-tools-gui
Icon=pdf-tools
Terminal=false
Categories=Office;Utility;
DESKTOP

chmod 755 %{buildroot}/opt/pdf-tools/pdf-tools
chmod 755 %{buildroot}/opt/pdf-tools/pdf-tools-gui
chmod 755 %{buildroot}/usr/bin/pdf-tools
chmod 755 %{buildroot}/usr/bin/pdf-tools-gui
chmod 644 %{buildroot}/usr/share/applications/pdf-tools.desktop
chmod 644 %{buildroot}/usr/share/icons/hicolor/256x256/apps/pdf-tools.png

%post
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi

%postun
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi

%files
/opt/pdf-tools/pdf-tools
/opt/pdf-tools/pdf-tools-gui
/usr/bin/pdf-tools
/usr/bin/pdf-tools-gui
/usr/share/applications/pdf-tools.desktop
/usr/share/icons/hicolor/256x256/apps/pdf-tools.png
EOF

rpmbuild --define "_topdir $RPM_TOP" -bb "$SPEC_FILE"

echo "RPM package:"
find "$RPM_TOP/RPMS" -name "*.rpm" -print
