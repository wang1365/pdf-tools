# CODEBUDDY.md

This file provides guidance to CodeBuddy when working with code in this
repository.

## Distribution Compatibility Covenant

This project is distributed to customer Kylin Linux machines. Packaging and
runtime choices must prioritize low-glibc Linux ARM64 compatibility.

- Prefer runtime dependencies with PyPI wheels for Linux `aarch64` using
  `manylinux2014_aarch64` / glibc 2.17, or a lower/equivalent baseline.
- Do not add runtime dependencies that only publish Linux `aarch64` wheels
  requiring newer baselines such as `manylinux_2_31` or `manylinux_2_39`
  unless the target Kylin release and packaging path are explicitly verified.
- Do not require customer machines to install system Qt, PySide, PyQt, or other
  desktop UI runtime packages for the distributed application.
- GUI dependencies must be bundled into the application package. The current
  GUI toolkit is Dear PyGui because it provides `manylinux2014_aarch64` wheels.
- Keep CLI/core PDF processing code independent from the GUI toolkit where
  practical.

## Commands

### Install Dependencies

```bash
uv sync
```

Or with pip:

```bash
pip install -e .
```

### Run CLI

```bash
pdf-tools input.pdf -o output.docx [--start N] [--end N] [--overwrite]
```

Or directly:

```bash
python -m pdf_tools input.pdf -o output.docx
```

### Run GUI Application

```bash
pdf-tools-gui
```

Or:

```bash
python -m pdf_tools.gui_main
```

### Build Standalone Executables

```bash
bash scripts/build_linux.sh
```

This produces `dist/pdf-tools` and `dist/pdf-tools-gui`. The GUI binary uses
Dear PyGui. The `--collect-all` flags for Dear PyGui, PyMuPDF, numpy, and lxml
are required for correct PyInstaller bundling.

### Build Kylin RPM Package

```bash
bash scripts/build_kylin_rpm.sh
```

The RPM is written under `build/rpmbuild/RPMS/`.

### Generate App Icons

```bash
python scripts/gen_icon.py
python scripts/svg_to_icons.py
```

## Architecture

### Dual Entry Points

The package has two entry points defined in `pyproject.toml`:

- CLI (`pdf-tools`): `pdf_tools.__main__:main`, an argparse-based CLI for
  PDF-to-DOCX conversion.
- GUI (`pdf-tools-gui`): `pdf_tools.gui_main:main`, a Dear PyGui desktop
  application with all tools.

### Core Module

`pdf_tools/converter.py` contains `convert_pdf_to_docx()`, the library-level
PDF-to-DOCX helper. It wraps `pdf2docx.Converter` with path validation and
directory creation.

### GUI Structure

`pdf_tools/gui_dpg.py` defines the Dear PyGui application with a left tool
selector and a right content area. Long-running PDF work runs on background
threads so the GUI remains responsive.

New GUI work should use Dear PyGui or toolkit-independent service functions.

### PDF Processing Libraries

- Merge: `pypdf`
- Split: `pypdf`
- Compress: `pypdf`
- Encrypt: `pypdf`
- PDF to Word: `pdf2docx`
- PDF to Images: `PyMuPDF` + `Pillow`
- PDF to PPT: `PyMuPDF` + `python-pptx`
- PDF to Excel: placeholder, not implemented

### Key Dependency Versions

Python 3.10+ is required. The project uses `setuptools` as the build backend.
