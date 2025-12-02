from pathlib import Path
from cairosvg import svg2png
from PIL import Image

def main() -> None:
    prefer = Path("assets/icon/app_sci.svg")
    svg = prefer if prefer.exists() else Path("assets/icon/app.svg")
    out_dir = Path("assets/icon")
    png = out_dir / "app.png"
    ico = out_dir / "app.ico"
    svg2png(url=str(svg), write_to=str(png), output_width=512, output_height=512)
    img = Image.open(png)
    img.save(ico, format="ICO", sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    print(png)
    print(ico)

if __name__ == "__main__":
    main()
