##################################################################################
# Minify page-specific CSS files (home.css, index-page.css).                     #   
#--------------------------------------------------------------------------------#
# Requires: csscompressor (install with: pip install csscompressor)              #   
#                                                                                #   
# After running, manually update your HTML overrides to link to the              #   
# minified CSS files (.min.css).                                                 #   
#                                                                                #   
# Source files:                                                                  #   
#   material-overrides/assets/stylesheets/home.css                               #
#   material-overrides/assets/stylesheets/index-page.css                         #   
#                                                                                #      
# Generated files:                                                               #   
#   home.min.css                                                                 #   
#   index-page.min.css                                                           #   
#                                                                                #   
# Example override line:                                                         #   
#   <link rel="stylesheet" href="{{ 'assets/stylesheets/home.min.css' | url }}"> #
##################################################################################

import sys
from pathlib import Path

try:
    from csscompressor import compress
except ImportError:
    print("[error] Missing csscompressor. Install with: pip install csscompressor")
    sys.exit(1)

BASE = Path("material-overrides/assets/stylesheets")

PAIRS = [
    ("home.css", "home.min.css"),
    ("index-page.css", "index-page.min.css"),
]

def minify_one(src_name: str, dst_name: str) -> None:
    src = BASE / src_name
    dst = BASE / dst_name
    if not src.exists():
        print(f"[warn] {src} does not exist, skipping.")
        return
    css_in = src.read_text(encoding="utf-8")
    css_out = compress(css_in)
    dst.write_text(css_out, encoding="utf-8")
    print(f"[ok] {src} -> {dst} ({len(css_out)} bytes)")

def main() -> int:
    for src, dst in PAIRS:
        minify_one(src, dst)
    return 0

if __name__ == "__main__":
    sys.exit(main())