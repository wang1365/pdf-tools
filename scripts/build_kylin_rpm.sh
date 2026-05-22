#!/usr/bin/env bash
set -euo pipefail

APP_NAME="pdf-tools"
VERSION="0.1.0"
RELEASE="1"
ROOT="$(pwd)"
RPM_TOP="$ROOT/build/rpmbuild"
SPEC_FILE="$RPM_TOP/SPECS/${APP_NAME}.spec"

command -v rpmbuild >/dev/null 2>&1 || {
  echo "rpmbuild not found. Install it first: yum install -y rpm-build"
  exit 1
}

uv -V >/dev/null 2>&1 || {
  echo "uv not found"
  exit 1
}

rm -rf "$ROOT/dist" "$ROOT/build"
mkdir -p "$RPM_TOP/BUILD" "$RPM_TOP/BUILDROOT" "$RPM_TOP/RPMS" "$RPM_TOP/SOURCES" "$RPM_TOP/SPECS" "$RPM_TOP/SRPMS"

[ -d .venv ] || uv venv --python python3
uv sync
uv pip install pyinstaller

uv run pyinstaller \
  -F \
  -n pdf-tools-gui \
  --windowed \
  --clean \
  --noconfirm \
  --collect-all dearpygui \
  --collect-all PyMuPDF \
  --collect-all numpy \
  --collect-all lxml \
  pdf_tools/gui_main.py

cat > "$SPEC_FILE" <<EOF
Name:           pdf-tools
Version:        $VERSION
Release:        $RELEASE%{?dist}
Summary:        PDF Tools desktop application
License:        Proprietary

%description
PDF conversion and processing tools.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/pdf-tools
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps

cp "$ROOT/dist/pdf-tools-gui" %{buildroot}/opt/pdf-tools/pdf-tools-gui
cp "$ROOT/assets/icon/app.png" %{buildroot}/usr/share/icons/hicolor/256x256/apps/pdf-tools.png

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

chmod 755 %{buildroot}/opt/pdf-tools/pdf-tools-gui
chmod 644 %{buildroot}/usr/share/applications/pdf-tools.desktop
chmod 644 %{buildroot}/usr/share/icons/hicolor/256x256/apps/pdf-tools.png

%files
/opt/pdf-tools/pdf-tools-gui
/usr/share/applications/pdf-tools.desktop
/usr/share/icons/hicolor/256x256/apps/pdf-tools.png
EOF

rpmbuild --define "_topdir $RPM_TOP" -bb "$SPEC_FILE"

echo "RPM package:"
find "$RPM_TOP/RPMS" -name "*.rpm" -print
