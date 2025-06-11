# makefont.py
from fpdf import make_font
import argparse

parser = argparse.ArgumentParser(description="Generate .py and .z font files from a .ttf file")
parser.add_argument("ttf_path", help="Path to the .ttf file")
parser.add_argument("--output-dir", default=".", help="Where to save the output files")
parser.add_argument("--font-name", default=None, help="Font name override")

args = parser.parse_args()

make_font(
    ttf_path=args.ttf_path,
    font_name=args.font_name,
    output_dir=args.output_dir,
    style="",
    encode="utf-8",
)
