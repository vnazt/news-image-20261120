#!/usr/bin/env python3
"""main.py -- grader entrypoint for news-image-20261120 (stdlib only).

Copies the committed entry.png (drawn by frontpage.py) into the output
directory. On any failure it copies fallback.png (the previous page)
instead, so the run always produces a valid image.
"""

import os
import shutil


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    dst = os.path.join(out_dir, "entry.png")
    try:
        os.makedirs(out_dir, exist_ok=True)
        shutil.copyfile(os.path.join(here, "entry.png"), dst)
    except Exception:
        try:
            os.makedirs(out_dir, exist_ok=True)
            shutil.copyfile(os.path.join(here, "fallback.png"), dst)
        except Exception:
            pass


if __name__ == "__main__":
    main()
