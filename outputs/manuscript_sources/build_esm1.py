"""Build anonymous Online Resource 1 from the three journal vector PDFs.

Run from any directory:
    python outputs/manuscript_sources/build_esm1.py

Dependencies: reportlab and pypdf. Arial regular/bold TTF files are read from
the Windows Fonts directory by default; use --font-dir elsewhere. Regenerate
the source figures first with figures_dysphagia.R if their result inputs change.
The output preserves vector artwork, embeds fonts, and puts each complete
caption below its figure on one A4 page. Rebuilding requires visual QA again.
"""
from __future__ import annotations

import argparse
import hashlib
from html import escape
from io import BytesIO
import json
import os
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import ContentStream, NameObject
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


def build(font_dir: Path, output: Path) -> dict:
    root = Path(__file__).resolve().parents[2]
    folder = root / "outputs/dysphagia/figures"
    caption_text = (folder / "Figure_captions.txt").read_text(encoding="utf-8")
    for i in range(1, 4):
        assert f"Online Resource 1, Fig. S{i}" in caption_text

    pdfmetrics.registerFont(TTFont("ArtworkArial", str(font_dir / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("ArtworkArialBold", str(font_dir / "arialbd.ttf")))
    title_style = ParagraphStyle(
        "FigureTitle", fontName="ArtworkArialBold", fontSize=10,
        leading=12.5, textColor="#17252E",
    )
    body_style = ParagraphStyle(
        "FigureCaption", fontName="ArtworkArial", fontSize=9.5,
        leading=12.3, textColor="#17252E",
    )
    page_width, page_height = A4
    figure_width = 174 * mm
    left = (page_width - figure_width) / 2
    writer = PdfWriter()
    page_checks = []
    contrast = caption_text.split(
        "Related estimates for Online Resource 1, Fig. S2:", 1
    )[1].split("\n\nSoftware:", 1)[0].strip()

    for number in range(1, 4):
        section = caption_text.split(f"Online Resource 1, Fig. S{number} ", 1)[1]
        if number < 3:
            section = section.split(f"Online Resource 1, Fig. S{number + 1} ", 1)[0]
        else:
            section = section.split("Related estimates for", 1)[0]
        title, body = section.split("NHIS 2025", 1)
        title = f"Fig. S{number} " + " ".join((title + "NHIS 2025").split())
        body = " ".join(body.split())
        if number == 2:
            body += " Related estimates: " + contrast

        buffer = BytesIO()
        document = canvas.Canvas(buffer, pagesize=A4, pageCompression=1, invariant=1)
        document.setTitle("Online Resource 1: Supplementary figures")
        document.setAuthor("")
        document.setCreator("")
        document.setFont("ArtworkArialBold", 11)
        document.setFillColor("#17252E")
        document.drawString(left, page_height - 38, "Online Resource 1")

        source = PdfReader(folder / f"ESM1_Fig{number}.pdf").pages[0]
        scale = figure_width / float(source.mediabox.width)
        figure_height = float(source.mediabox.height) * scale
        figure_bottom = page_height - 62 - figure_height
        caption_top = figure_bottom - 18
        heading = Paragraph(escape(title), title_style)
        _, heading_height = heading.wrap(figure_width, 400)
        heading.drawOn(document, left, caption_top - heading_height)
        paragraph = Paragraph(escape(body), body_style)
        _, body_height = paragraph.wrap(figure_width, 400)
        caption_bottom = caption_top - heading_height - 8 - body_height
        assert caption_bottom > 48, f"Caption overflows page {number}"
        paragraph.drawOn(document, left, caption_bottom)
        document.setFont("ArtworkArial", 8)
        document.drawRightString(page_width - left, 28, f"{number} / 3")
        document.showPage()
        document.save()
        buffer.seek(0)
        page = PdfReader(buffer).pages[0]
        page.merge_transformed_page(
            source, Transformation().scale(scale).translate(left, figure_bottom)
        )
        writer.add_page(page)
        page_checks.append({
            "page": number, "figure_width_mm": figure_width / mm,
            "caption_words": len(body.split()),
            "caption_bottom_pt": round(caption_bottom, 2),
        })

    metadata = {
        "/Title": "Online Resource 1: Supplementary figures",
        "/Author": "", "/Subject": "Supplementary figures S1-S3 and full captions",
        "/Creator": "", "/Producer": "",
    }
    writer.add_metadata(metadata)
    assembled = BytesIO()
    writer.write(assembled)
    assembled.seek(0)
    reader = PdfReader(assembled)
    final_writer = PdfWriter()
    for page in reader.pages:
        fonts = page["/Resources"]["/Font"]
        unused = [
            key for key, ref in fonts.items()
            if ref.get_object().get("/BaseFont") == "/Helvetica"
        ]
        embedded = next(
            key for key, ref in fonts.items()
            if "ArialMT" in str(ref.get_object().get("/BaseFont", ""))
        )
        contents = ContentStream(page["/Contents"], reader)
        # ReportLab selects unused default Helvetica before drawing any text.
        # Keep all font resources embedded by selecting the existing Arial face.
        for operands, operator in contents.operations:
            if operator == b"Tf" and operands[0] in unused:
                operands[0] = NameObject(embedded)
        page[NameObject("/Contents")] = contents
        for key in unused:
            del fonts[key]
        final_writer.add_page(page)
    final_writer.add_metadata(metadata)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        final_writer.write(handle)

    final = PdfReader(output)
    assert len(final.pages) == 3
    assert all(not str(final.metadata.get(key, "")) for key in ("/Author", "/Creator", "/Producer"))
    for number, page in enumerate(final.pages, 1):
        text = page.extract_text()
        assert f"Fig. S{number}" in text and "Online Resource 1" in text
        for reference in page["/Resources"]["/Font"].values():
            font = reference.get_object()
            descriptor = font.get("/FontDescriptor")
            if descriptor is None and "/DescendantFonts" in font:
                descriptor = font["/DescendantFonts"][0].get_object().get("/FontDescriptor")
            assert descriptor is not None
            assert any(key in descriptor.get_object() for key in ("/FontFile", "/FontFile2", "/FontFile3"))
    return {
        "output": str(output), "bytes": output.stat().st_size,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "pages": page_checks,
        "visual_review": "Required after rebuilding; this script performs structural checks only",
    }


if __name__ == "__main__":
    project = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font-dir", type=Path,
                        default=Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts")
    parser.add_argument("--output", type=Path,
                        default=project / "outputs/dysphagia/ESM1.pdf")
    arguments = parser.parse_args()
    print(json.dumps(build(arguments.font_dir, arguments.output), indent=2))
