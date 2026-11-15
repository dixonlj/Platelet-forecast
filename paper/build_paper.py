#!/usr/bin/env python3
"""Build a draft and its supplement (.md with numbered Vancouver citations, and .docx) with pandoc --citeproc."""
import re, subprocess
from pathlib import Path
import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

P = Path(__file__).resolve().parent
REF = P / "reference_draft.docx"

def make_reference(header="DRAFT — educational, not peer reviewed. Not clinical or ordering advice."):
    subprocess.run(["pandoc", "-o", str(REF), "--print-default-data-file", "reference.docx"], check=True)
    d = docx.Document(str(REF))
    for sec in d.sections:
        for hf in (sec.header, sec.footer):
            hf.is_linked_to_previous = False
            par = hf.paragraphs[0] if hf.paragraphs else hf.add_paragraph()
            par.text = ""
            r = par.add_run(header)
            r.bold = True; r.font.size = Pt(9); r.font.color.rgb = RGBColor(0xB0, 0x00, 0x00)
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    d.save(str(REF))

def fill(name):
    s = (P / f"{name}.src.md").read_text()
    s = re.sub(r"\{\{TABLE:(\w+)\}\}", lambda m: (P / "tables" / f"{m.group(1)}.md").read_text(), s)
    tmp = P / f".{name}.filled.md"
    tmp.write_text(s)
    return tmp

def paper_charts(text):
    """Layout build: use the paper-size redraws in charts/paper/ (scripts/25_charts_paper.py) when present,
    at their native printed width (max 6.0 in) so chart fonts print at their drawn size."""
    from PIL import Image
    def sub(m):
        name = m.group(1)
        alt = P.parent / "charts" / "paper" / name
        if not alt.exists():
            return m.group(0)
        im = Image.open(alt)
        dpi = (im.info.get("dpi") or (300, 300))[0] or 300
        w = min(im.size[0] / dpi, 6.0)
        return f"(../charts/paper/{name}){{width={w:.2f}in}}"
    return re.sub(r"\(\.\./charts/([\w.-]+\.png)\)\{width=100%\}", sub, text)

def pdf_last_page_lines(pdf):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    t = subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    lines = [l for l in t.splitlines() if l.strip()]
    return max(0, len(lines) - 2), n   # minus header and page number

def build_layout(name, line_numbers=False):
    """Journal-style layout copy: <name>_layout.docx and .pdf. Same source text; the plain build is untouched.
    If the last page would hold fewer than 10 lines, the reference list is tightened (up to 2 steps)."""
    from layout_docx import polish
    src = fill(name)
    src.write_text(paper_charts(src.read_text()))
    raw = P / f".{name}_layout_raw.docx"
    out = P / f"{name}_layout.docx"
    subprocess.run(["pandoc", str(src.name), "--citeproc", "--resource-path=.:..", "-M", "reference-section-title=References",
                    "--reference-doc", REF.name, "-o", raw.name], check=True, cwd=P)
    src.unlink()
    for level in (0, 1, 2):
        rep = polish(str(raw), str(out), "Educational analysis of public data. Not clinical or ordering advice.",
                     line_numbers, bib_level=level)
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(P), str(out)],
                       check=True, cwd=P, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        lines, pages = pdf_last_page_lines(P / f"{name}_layout.pdf")
        if lines >= 10:
            break
    raw.unlink()
    (P / "layout_preview").mkdir(exist_ok=True)
    (P / "layout_preview" / f"{name}_minus_signs.txt").write_text(
        f"{len(rep['minus'])} hyphen-minus signs converted to U+2212 (context shown):\n" + "\n".join(rep["minus"]) + "\n")
    print(f"{name}: {pages} pages; last page {lines} text lines; bibliography level {level}; "
          f"{len(rep['minus'])} minus signs converted")

def build(name):
    src = fill(name)
    common = ["pandoc", str(src.name), "--citeproc", "--resource-path=.:..", "-M", "reference-section-title=References"]
    subprocess.run(common + ["-M", "link-citations=false", "-t", "markdown-citations-simple_tables-multiline_tables-grid_tables-raw_html-fenced_divs-native_divs-bracketed_spans-native_spans-link_attributes-header_attributes", "--wrap=none", "--standalone", "-o", f"{name}.md"], check=True, cwd=P)
    subprocess.run(common + ["--reference-doc", REF.name, "-o", f"{name}.docx"], check=True, cwd=P)
    src.unlink()

if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ver = args[0] if args else "v3"
    # v4 onward: posting version; medRxiv adds its own "not peer reviewed" banner.
    make_reference() if ver in ("v1", "v2", "v3") else make_reference("Educational analysis of public data. Not clinical or ordering advice.")
    for n in (f"draft_{ver}", f"supplement_{ver}"):
        vnum = int(ver.lstrip("v")) if ver.lstrip("v").isdigit() else 0
        # v10 onward use only charts/m10_*.png (no paper-size redraws), so script 25 is not needed; it also needs
        # per-run files that are not in the public repository. Force it with --redraw-old-charts.
        if "--layout" in sys.argv and n.startswith("draft_") and (vnum < 10 or "--redraw-old-charts" in sys.argv):
            subprocess.run([sys.executable, str(P.parent / "scripts" / "25_charts_paper.py")], check=True)
            if ver >= "v6":   # v6 figures (year-labelled gaps, service level, delivery calendar)
                subprocess.run([sys.executable, str(P.parent / "scripts" / "31_charts_v6.py")], check=True)
        if "--layout" in sys.argv:   # python3 build_paper.py v5 --layout [--line-numbers]
            build_layout(n, "--line-numbers" in sys.argv)
        else:
            build(n)
    print("built", ver, "(layout)" if "--layout" in sys.argv else "")
