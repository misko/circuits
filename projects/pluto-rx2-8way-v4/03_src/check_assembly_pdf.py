#!/usr/bin/env python3
"""Regression gate for the RX2 v4 assembly/rework PDF."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


EXPECTED_REFS = {
    "C_BULK", "C_SW1", "C_SW2", "FB_3V3", "H1", "H2", "H3", "H4",
    "J_ANT1", "J_ANT2", "J_ANT3", "J_ANT4", "J_ANT5", "J_ANT6",
    "J_ANT7", "J_ANT8", "J_RX1", "J_RX2", "LED_ST", "R_LED", "R_PD1",
    "R_PD2", "R_PD3", "R_PD4", "R_S1", "R_S2", "R_S3", "R_S4", "R_T1",
    "R_T2", "U_MCU", "U_SW",
}
SWITCH_REFS = {"U_SW", "R_PD1", "R_PD2", "R_PD3", "R_PD4", "C_SW1", "C_SW2"}
MODULE_REFS = {"U_MCU", "LED_ST", "R_LED", "R_S1", "R_S2", "R_S3", "R_S4", "C_BULK", "FB_3V3"}


def fail(message: str) -> None:
    raise RuntimeError(f"ASSEMBLY-PDF FAIL: {message}")


def words_by_page(pdf: Path) -> list[list[tuple[str, tuple[float, float, float, float]]]]:
    with tempfile.TemporaryDirectory(prefix="assembly-pdf-check-") as td:
        xml_path = Path(td) / "bbox.xml"
        with xml_path.open("wb") as stream:
            subprocess.run(
                ["pdftotext", "-bbox-layout", str(pdf), "-"],
                stdout=stream,
                check=True,
            )
        root = ET.parse(xml_path).getroot()

    pages: list[list[tuple[str, tuple[float, float, float, float]]]] = []
    for page in root.iter("{http://www.w3.org/1999/xhtml}page"):
        words = []
        for word in page.iter("{http://www.w3.org/1999/xhtml}word"):
            words.append(
                (
                    word.text or "",
                    tuple(float(word.attrib[k]) for k in ("xMin", "yMin", "xMax", "yMax")),
                )
            )
        pages.append(words)
    return pages


def overlaps(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    # A small tolerance prevents font-boundary rounding from inventing a hit.
    return a[0] < b[2] - 0.5 and b[0] < a[2] - 0.5 and a[1] < b[3] - 0.5 and b[1] < a[3] - 0.5


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} ASSEMBLY.pdf", file=sys.stderr)
        return 2
    pdf = Path(sys.argv[1])
    if not pdf.is_file() or pdf.stat().st_size == 0:
        fail(f"missing or empty artifact: {pdf}")

    pages = words_by_page(pdf)
    if len(pages) != 3:
        fail(f"expected 3 useful pages (overview + two details), found {len(pages)}")
    if any(not page for page in pages):
        fail("one or more pages has no searchable text")

    overview_refs = [word for word, _ in pages[0] if word in EXPECTED_REFS]
    missing = EXPECTED_REFS - set(overview_refs)
    duplicates = sorted(ref for ref in EXPECTED_REFS if overview_refs.count(ref) != 1)
    if missing:
        fail(f"overview missing refdes: {sorted(missing)}")
    if duplicates:
        fail(f"overview must contain each refdes exactly once: {duplicates}")

    for page_number, page in enumerate(pages, 1):
        ref_words = [(word, box) for word, box in page if word in EXPECTED_REFS]
        for index, (left_word, left_box) in enumerate(ref_words):
            for right_word, right_box in ref_words[index + 1 :]:
                if overlaps(left_box, right_box):
                    fail(
                        f"page {page_number} overlapping refdes: "
                        f"{left_word} and {right_word}"
                    )

    page2 = {word for word, _ in pages[1]}
    page3 = {word for word, _ in pages[2]}
    if not SWITCH_REFS <= page2:
        fail(f"switch detail missing: {sorted(SWITCH_REFS - page2)}")
    if not MODULE_REFS <= page3:
        fail(f"module detail missing: {sorted(MODULE_REFS - page3)}")

    text = " ".join(word for page in pages for word, _ in page)
    forbidden_values = ("220Ω", "10kΩ", "100nF", "1uF", "680Ω", "C504007", "C5121458")
    found_values = [value for value in forbidden_values if re.search(re.escape(value), text)]
    if found_values:
        fail(f"component values leaked into refdes-only drawing: {found_values}")

    print(
        "ASSEMBLY-PDF PASS: 3/3 nonblank pages; 32/32 overview refs unique; "
        "0 refdes overlaps; values suppressed; both detail censuses complete"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
