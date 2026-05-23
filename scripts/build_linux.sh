#!/usr/bin/env bash
set -e
uv -V >/dev/null 2>&1 || { echo "uv not found"; exit 1; }
[ -d .venv ] || uv venv
uv sync
uv pip install pyinstaller
uv run pyinstaller -F -n pdf-tools --clean --noconfirm --collect-all PyMuPDF --collect-all numpy --collect-all lxml pdf_tools/__main__.py
echo dist/pdf-tools
