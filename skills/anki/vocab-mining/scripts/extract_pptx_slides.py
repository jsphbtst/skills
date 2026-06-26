#!/usr/bin/env python3
"""Extract slide text from a (potentially huge) .pptx without unzipping media.

Lesson/lecture .pptx files are often 100 MB+ because of embedded audio, video,
and images. For vocab/term mining only the slide XML is needed, so this unzips
just `ppt/slides/*.xml` and parses <a:p> paragraphs / <a:t> text runs,
preserving slide order. Output is grouped per slide so structure (term lists,
per-item slides, summary/grammar slides) stays visible. Language-agnostic.

Usage:
    python3 extract_pptx_slides.py "<file>.pptx"
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile


def slide_num(path):
    return int(re.search(r"\d+", os.path.basename(path)).group())


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: extract_pptx_slides.py <file.pptx>")
    pptx = sys.argv[1]
    if not os.path.exists(pptx):
        sys.exit(f"no such file: {pptx}")

    tmp = tempfile.mkdtemp(prefix="pptx-slides-")
    try:
        # Extract ONLY the slide XML — never the whole archive (media is huge).
        subprocess.run(
            ["unzip", "-o", pptx, "ppt/slides/*.xml", "-d", tmp],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        slides = sorted(
            glob.glob(os.path.join(tmp, "ppt/slides/slide*.xml")), key=slide_num
        )
        for f in slides:
            with open(f, encoding="utf-8") as fh:
                xml = fh.read()
            lines = []
            for para in re.findall(r"<a:p>.*?</a:p>", xml, re.S):
                text = "".join(re.findall(r"<a:t>(.*?)</a:t>", para, re.S)).strip()
                if text:
                    lines.append(text)
            if lines:
                print(f"===== slide{slide_num(f)} =====")
                print("\n".join(lines))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
