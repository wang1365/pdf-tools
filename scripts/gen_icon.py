from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)

def make_icon_png(path: Path, size: int = 256) -> None:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(size * 0.21875)
    for y in range(size):
        t = y / (size - 1)
        c = (_lerp(13, 66, t), _lerp(71, 165, t), _lerp(161, 245, t), 255)
        d.rounded_rectangle((0, y, size, y + 1), r, fill=c)
    hl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse((int(size*0.18), int(size*0.06), int(size*0.82), int(size*0.60)), fill=(255,255,255,30))
    hl = hl.filter(ImageFilter.GaussianBlur(radius=int(size*0.06)))
    img.alpha_composite(hl)
    bx, by = int(size*0.12), int(size*0.08)
    bw, bh = int(size*0.76), int(size*0.84)
    body_shadow = Image.new("RGBA", (size, size), (0,0,0,0))
    bs = ImageDraw.Draw(body_shadow)
    bs.ellipse((bx+4, by+8, bx+bw+4, by+bh+8), fill=(0,0,0,65))
    body_shadow = body_shadow.filter(ImageFilter.GaussianBlur(radius=int(size*0.03)))
    img.alpha_composite(body_shadow)
    d.ellipse((bx, by, bx+bw, by+bh), fill=(255,255,255,245))
    hx = bx+int(bw*0.26)
    hy = by+int(bh*0.02)
    hw = int(bw*0.48)
    hh = int(bh*0.33)
    d.ellipse((hx, hy, hx+hw, hy+hh), fill=(255,255,255,245))
    eye_r = int(size*0.016)
    ex1 = hx+int(hw*0.28)
    ey = hy+int(hh*0.38)
    ex2 = hx+int(hw*0.72)
    d.ellipse((ex1-eye_r, ey-eye_r, ex1+eye_r, ey+eye_r), fill=(35,35,35,255))
    d.ellipse((ex2-eye_r, ey-eye_r, ex2+eye_r, ey+eye_r), fill=(35,35,35,255))
    beak = [(hx+int(hw*0.50), hy+int(hh*0.52)), (hx+int(hw*0.62), hy+int(hh*0.62)), (hx+int(hw*0.50), hy+int(hh*0.72))]
    d.polygon(beak, fill=(255,255,255,245))
    wing_l = [(bx+int(bw*0.12), by+int(bh*0.46)), (bx+int(bw*0.30), by+int(bh*0.70)), (bx+int(bw*0.10), by+int(bh*0.78))]
    wing_r = [(bx+int(bw*0.88), by+int(bh*0.46)), (bx+int(bw*0.70), by+int(bh*0.70)), (bx+int(bw*0.90), by+int(bh*0.78))]
    d.polygon(wing_l, fill=(255,255,255,245))
    d.polygon(wing_r, fill=(255,255,255,245))
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
