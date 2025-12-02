from pathlib import Path
from PIL import Image, ImageDraw

def make_icon_png(path: Path, size: int = 256) -> None:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = 48
    d.rounded_rectangle((0, 0, size, size), r, fill=(25, 118, 210, 255))
    doc_w, doc_h = int(size*0.47), int(size*0.62)
    doc_x, doc_y = int(size*0.22), int(size*0.16)
    d.rounded_rectangle((doc_x, doc_y, doc_x+doc_w, doc_y+doc_h), int(size*0.05), fill=(255,255,255,255))
    fold_x, fold_y = doc_x+doc_w, doc_y
    d.polygon([(fold_x, fold_y), (fold_x, fold_y+int(size*0.18)), (fold_x-int(size*0.18), fold_y)], fill=(187, 222, 251, 255))
    base_y = doc_y+int(size*0.44)
    d.polygon([(doc_x+int(size*0.10), base_y), (doc_x+int(size*0.17), base_y-int(size*0.22)), (doc_x+int(size*0.22), base_y), (doc_x+int(size*0.28), base_y-int(size*0.22)), (doc_x+int(size*0.34), base_y), (doc_x+int(size*0.40), base_y-int(size*0.22)), (doc_x+int(size*0.46), base_y)], fill=(25,118,210,255))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG")

def make_icon_ico(png_path: Path, ico_path: Path) -> None:
    img = Image.open(png_path)
    sizes = [(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
    img.save(ico_path, format="ICO", sizes=sizes)

def main() -> None:
    out_dir = Path("assets/icon")
    png_path = out_dir/"app.png"
    ico_path = out_dir/"app.ico"
    make_icon_png(png_path)
    make_icon_ico(png_path, ico_path)
    print(png_path)
    print(ico_path)

if __name__ == "__main__":
    main()
