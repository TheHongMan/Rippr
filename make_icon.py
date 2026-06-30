"""Rasterize rippr_icon.svg into a multi-resolution rippr.ico for the exe + shortcut."""
import io
from PIL import Image

SVG = "rippr_icon.svg"
OUT = "rippr.ico"
SIZES = [16, 24, 32, 48, 64, 128, 256]


def render_base():
    # PyMuPDF bundles its own renderer (alpha-capable, no system deps).
    import fitz
    doc = fitz.open(SVG)
    page = doc[0]
    zoom = 256.0 / max(page.rect.width, page.rect.height)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGBA")


def main():
    base = render_base()
    base.save(OUT, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"Wrote {OUT} from {base.size[0]}px base, sizes {SIZES}")


if __name__ == "__main__":
    main()
