# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## Commands

### Install dependencies
```bash
uv sync
```
Or with pip: `pip install -e .`

### Run CLI (PDF to Word conversion)
```bash
pdf-tools input.pdf -o output.docx [--start N] [--end N] [--overwrite]
```
Or directly: `python -m pdf_tools input.pdf -o output.docx`

### Run GUI application
```bash
pdf-tools-gui
```
Or: `python -m pdf_tools.gui_main`

### Build standalone executable (Linux)
```bash
bash scripts/build_linux.sh
```
Uses `uv` + PyInstaller to produce a single-file binary at `dist/pdf-tools`. The `--collect-all` flags for PyMuPDF, numpy, and lxml are required for correct bundling.

### Generate app icons
```bash
python scripts/gen_icon.py    # Procedural icon generation via PIL
python scripts/svg_to_icons.py  # SVG→PNG/ICO conversion via cairosvg
```

## Architecture

### Dual entry points
The package has two entry points defined in `pyproject.toml`:
- **CLI** (`pdf-tools`): `pdf_tools.__main__:main` — argparse-based CLI for PDF→DOCX conversion only.
- **GUI** (`pdf-tools-gui`): `pdf_tools.gui_main:main` — PySide6 desktop application with all tools.

### Core module
`pdf_tools/converter.py` contains `convert_pdf_to_docx()`, the sole library-level function. It wraps `pdf2docx.Converter` with path validation and directory creation. This is the only function exported from the package (`__init__.py`).

### GUI structure
`pdf_tools/gui.py` defines `MainWindow`, a PySide6 `QMainWindow` with a left sidebar (`QListWidget`) and a right content area (`QStackedWidget`). Each tool is a page widget added to the stack; sidebar row changes switch the displayed page.

### Page widget pattern
Each page in `pdf_tools/pages/` follows a consistent pattern:
1. **Page class** (`PdfXxxPage(QWidget)`) — builds the UI layout and handles user interaction.
2. **Worker thread class** (`XxxThread(QThread)`) — performs the actual PDF operation off the main thread to keep the GUI responsive.

The thread communication uses two PySide6 `Signal`s: `finished_signal(str)` for the output path on success, and `error_signal(str)` for error messages. The page connects these to `on_finished`/`on_error` slots, plus `thread.finished→on_thread_done` to hide the progress bar and re-enable buttons.

### DropArea widget
Most pages define a local `DropArea(QLabel)` subclass supporting click-to-browse and drag-and-drop for PDF file selection. This class is duplicated across multiple page files rather than shared — any changes to it need to be applied to all copies.

### PDF processing libraries used per page
- **pdf_merge**: `pypdf` (PdfReader/PdfWriter)
- **pdf_split**: `pypdf`
- **pdf_compress**: `pypdf` (compress_content_streams, compress_identical_objects)
- **pdf_encrypt**: `pypdf` (encrypt with AES-256)
- **pdf_to_word**: `pdf2docx` via `converter.py`
- **pdf_to_image**: `PyMuPDF` (fitz) + `Pillow`
- **pdf_to_ppt**: `PyMuPDF` (fitz) + `python-pptx`
- **pdf_to_excel**: placeholder, not yet implemented

### Key dependency versions
Python ≥3.12 is required. The project uses `setuptools` as the build backend.
