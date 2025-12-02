import argparse
import sys
from pathlib import Path
from pdf_tools.converter import convert_pdf_to_docx

def main() -> int:
    p = argparse.ArgumentParser(prog="pdf-tools", description="Convert PDF to Word")
    p.add_argument("input", help="Input PDF file path")
    p.add_argument("-o", "--output", help="Output DOCX file path")
    p.add_argument("--start", type=int, help="Start page index (0-based)")
    p.add_argument("--end", type=int, help="End page index (inclusive)")
    p.add_argument("--overwrite", action="store_true", help="Overwrite if output exists")
    args = p.parse_args()

    inp = Path(args.input)
    if not inp.is_file():
        sys.stderr.write("Input file not found\n")
        return 1
    out = Path(args.output) if args.output else inp.with_suffix(".docx")
    if out.exists() and not args.overwrite:
        sys.stderr.write("Output file exists. Use --overwrite to replace\n")
        return 2

    try:
        convert_pdf_to_docx(str(inp), str(out), start=args.start, end=args.end)
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        return 3

    sys.stdout.write(str(out) + "\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
