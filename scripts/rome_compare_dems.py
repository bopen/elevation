"""Render the Rome DEM comparison image of the README.

The ``GLO-30`` product needs the Earth Data Hub credentials in ``~/.netrc``. Run from
the repository root::

    uv run --frozen python scripts/rome_compare_dems.py [OUTPUT_FOLDER]
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import elevation

PRODUCTS = [
    ("GLO-30", "Copernicus DEM"),
    ("AW3D30", "ALOS World 3D"),
    ("SRTM1_GEOID", "SRTM GL1"),
]
# the README example
CLIP_BOUNDS = (12.35, 41.8, 12.65, 42.0)
# the Tiber from Prati to the Magliana meander, with Monte Mario on the west edge
BOUNDS = (12.446, 41.833, 12.511, 41.9363)
# without -novshift the EGM2008 heights of GLO-30 become ellipsoidal heights
WARP_OPTIONS = (
    "-q -overwrite -novshift -t_srs EPSG:32633 -te_srs EPSG:4326 -tr 10 10 -r cubic"
)
HILLSHADE_OPTIONS = "-q -of PNG -compute_edges -z 2.5 -az 315 -alt 40"
# hypsometric tints from sage green to warm tan, in metres
RAMP = """\
-20 157 191 140
10 157 191 140
35 190 210 158
60 222 228 182
90 238 230 196
130 230 210 170
250 214 188 150
"""
GAP = 8


def run(*args: str | Path) -> None:
    subprocess.run([str(arg) for arg in args], check=True)


def shade(product: str, folder: Path) -> tuple[Path, Path]:
    """Clip the product and render its hillshade and colour relief as PNG files."""
    dem = folder / f"{product}.tif"
    elevation.clip(CLIP_BOUNDS, dem, product=product)
    utm = folder / f"{product}-utm.tif"
    bounds = [str(value) for value in BOUNDS]
    run("gdalwarp", *WARP_OPTIONS.split(), "-te", *bounds, dem, utm)
    hillshade = folder / f"{product}-hillshade.png"
    run("gdaldem", "hillshade", *HILLSHADE_OPTIONS.split(), utm, hillshade)
    ramp = folder / "ramp.txt"
    ramp.write_text(RAMP)
    relief = folder / f"{product}-relief.png"
    run("gdaldem", "color-relief", "-q", "-of", "PNG", utm, ramp, relief)
    return hillshade, relief


def panel(hillshade: Path, relief: Path, label: str, width: int) -> Image.Image:
    """Blend the colour relief with the hillshade, crop it to width and label it."""
    light = np.asarray(Image.open(hillshade).convert("L"), dtype=float) / 255
    color = np.asarray(Image.open(relief).convert("RGB"), dtype=float)
    blend = np.clip(color * (0.25 + 0.85 * light)[..., None], 0, 255).astype("uint8")
    tile = Image.fromarray(blend[:, :width])
    draw = ImageDraw.Draw(tile, "RGBA")
    font = ImageFont.load_default(size=50)
    anchor = (tile.width // 2, 30)
    box = draw.multiline_textbbox(anchor, label, font=font, anchor="ma", align="center")
    frame = (box[0] - 24, box[1] - 16, box[2] + 24, box[3] + 16)
    draw.rounded_rectangle(frame, 18, fill=(255, 255, 255, 215))
    text_color = (30, 40, 30)
    draw.multiline_text(anchor, label, text_color, font, anchor="ma", align="center")
    return tile


def main(output_folder: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        shades = [shade(product, Path(tmp)) for product, _ in PRODUCTS]
        height = Image.open(shades[0][0]).height
        # three panels side by side in a 4:3 image
        width = (height * 4 // 3 - 2 * GAP) // 3
        canvas = Image.new("RGB", (3 * width + 2 * GAP, height), "white")
        for index, (product, name) in enumerate(PRODUCTS):
            hillshade, relief = shades[index]
            tile = panel(hillshade, relief, f"{name}\n{product}", width)
            canvas.paste(tile, (index * (width + GAP), 0))
    # 20 m pixels fit the README column and are still finer than the 30 m DEMs
    size = (canvas.width // 2, canvas.height // 2)
    canvas = canvas.resize(size, Image.Resampling.LANCZOS)
    path = output_folder / "rome-compare-dems.jpg"
    canvas.save(path, quality=80, optimize=True, progressive=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(Path(sys.argv[1]))
    else:
        main(Path())
