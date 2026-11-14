#!/usr/bin/env python3
"""Journal-style layout pass for a pandoc-built .docx (layout only: no text is added, removed or reworded).

Applied after pandoc in build_paper.py --layout. What it does:
- US Letter, 1-inch margins, single column; body Cambria 11 pt (LibreOffice renders it with the
  metric-compatible Caladea), 1.3 line spacing, widow/orphan control; headings Calibri (Carlito), black.
- Title block left-aligned; author line broken onto separate lines at its existing sentence breaks;
  ORCID and e-mail made clickable (link targets only, visible text unchanged).
- Opening disclaimer paragraph boxed and shaded.
- Header: the disclaimer in small grey type; footer: centred page number (the duplicate footer
  disclaimer is replaced by the page number).
- Tables: full text width, column widths sized to content, Calibri 9 pt (8 pt for very wide tables),
  booktabs-style rules, header row repeated on every page, rows never split, short tables kept on one
  page, caption above and kept with its table.
- Figures: centred, max 6.0 x 4.6 in, kept with the caption, caption below (not italic).
- References: Vancouver numbers with a hanging indent, 9.5 pt.
- Optional continuous line numbers (--line-numbers) for review copies.
"""
import copy, re, sys
import docx
from docx.shared import Pt, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.opc.constants import RELATIONSHIP_TYPE as RT

BODY = "Cambria"; HEAD = "Calibri"; TABLE = "Calibri"; MONO = "Consolas"
TEXT_W_IN = 6.5
TEXT_W = int(TEXT_W_IN * 1440)          # twips
LINE = 1.3
KEEP_WHOLE_ROWS = 12

def el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn(k), str(v))
    return e

def set_rfonts(rpr, name):
    for old in rpr.findall(qn("w:rFonts")):
        rpr.remove(old)
    rpr.insert(0, el("w:rFonts", **{"w:ascii": name, "w:hAnsi": name, "w:cs": name, "w:eastAsia": name}))

def set_color(rpr, hexrgb):
    for old in rpr.findall(qn("w:color")):
        rpr.remove(old)
    rpr.append(el("w:color", **{"w:val": hexrgb}))

def style(d, name):
    try:
        return d.styles[name]
    except KeyError:
        return None

def fmt_style(d, name, font=None, size=None, bold=None, italic=None, color=None, before=None, after=None,
              line=None, align=None, keep_next=None, left=None, hanging=None, widow=True):
    s = style(d, name)
    if s is None:
        return None
    rpr = s.element.get_or_add_rPr()
    if font:
        set_rfonts(rpr, font)
    if size is not None:
        s.font.size = Pt(size)
    if bold is not None:
        s.font.bold = bold
    if italic is not None:
        s.font.italic = italic
    if color:
        set_color(rpr, color)
    pf = getattr(s, "paragraph_format", None)
    if pf is not None:
        if before is not None: pf.space_before = Pt(before)
        if after is not None: pf.space_after = Pt(after)
        if line is not None: pf.line_spacing = line
        if align is not None: pf.alignment = align
        if keep_next is not None: pf.keep_with_next = keep_next
        if left is not None: pf.left_indent = Inches(left)
        if hanging is not None: pf.first_line_indent = Inches(-hanging)
        if widow: pf.widow_control = True
    return s

def styles(d):
    # document defaults: explicit fonts instead of theme fonts
    rpr_def = d.styles.element.find(qn("w:docDefaults")).find(qn("w:rPrDefault")).find(qn("w:rPr"))
    set_rfonts(rpr_def, BODY)
    for n in ("Normal", "Body Text", "First Paragraph"):
        fmt_style(d, n, font=BODY, size=11, before=0, after=6, line=LINE)
    fmt_style(d, "Compact", font=BODY, size=11, before=0, after=2, line=LINE)
    fmt_style(d, "Title", font=HEAD, size=17, bold=True, color="000000", before=0, after=10, line=1.1,
              align=WD_ALIGN_PARAGRAPH.LEFT, keep_next=True)
    fmt_style(d, "Subtitle", font=HEAD, size=13, color="000000", align=WD_ALIGN_PARAGRAPH.LEFT)
    fmt_style(d, "Author", font=HEAD, size=10.5, bold=False, color="000000", before=0, after=4, line=1.15,
              align=WD_ALIGN_PARAGRAPH.LEFT, keep_next=True)
    fmt_style(d, "Date", font=HEAD, size=10, bold=False, color="404040", before=0, after=12, line=1.15,
              align=WD_ALIGN_PARAGRAPH.LEFT, keep_next=True)
    fmt_style(d, "Heading 1", font=HEAD, size=13.5, bold=True, color="000000", before=18, after=6, line=1.1, keep_next=True)
    fmt_style(d, "Heading 2", font=HEAD, size=11.5, bold=True, color="000000", before=12, after=4, line=1.1, keep_next=True)
    fmt_style(d, "Heading 3", font=HEAD, size=11, bold=True, italic=True, color="000000", before=10, after=3, line=1.1, keep_next=True)
    for n in ("Heading 1", "Heading 2", "Heading 3"):
        s = style(d, n)
        if s is not None:
            s.paragraph_format.keep_together = True
    fmt_style(d, "Table Caption", font=HEAD, size=9.5, italic=False, color="000000", before=10, after=4, line=1.15, keep_next=True)
    fmt_style(d, "Image Caption", font=HEAD, size=9.5, italic=False, color="000000", before=4, after=14, line=1.15)
    fmt_style(d, "Captioned Figure", before=10, after=0, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER, keep_next=True)
    fmt_style(d, "Figure", before=10, after=0, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER, keep_next=True)
    fmt_style(d, "Bibliography", font=BODY, size=9.5, before=0, after=3, line=1.1, left=0.4, hanging=0.4)
    s = style(d, "Bibliography")
    if s is not None:
        ppr = s.element.get_or_add_pPr()
        for t in ppr.findall(qn("w:tabs")):
            ppr.remove(t)
        tabs = el("w:tabs"); tabs.append(el("w:tab", **{"w:val": "left", "w:pos": int(0.4 * 1440)}))
        ppr.append(tabs)
    for n in ("Hyperlink",):
        s = style(d, n)
        if s is not None:
            set_color(s.element.get_or_add_rPr(), "1F4E79")
    for n in ("Verbatim Char", "Source Code"):
        s = style(d, n)
        if s is not None:
            set_rfonts(s.element.get_or_add_rPr(), MONO); s.font.size = Pt(9)

def page_setup(d, header_text, line_numbers=False):
    for sec in d.sections:
        sec.page_width, sec.page_height = Inches(8.5), Inches(11)
        sec.left_margin = sec.right_margin = Inches(1)
        sec.top_margin = sec.bottom_margin = Inches(1)
        sec.header_distance = sec.footer_distance = Inches(0.45)
        # header: disclaimer, small grey
        hp = sec.header.paragraphs[0]
        for r in list(hp.runs):
            r._r.getparent().remove(r._r)
        r = hp.add_run(header_text); r.font.size = Pt(8); r.font.name = HEAD
        r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
        hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        hp.paragraph_format.space_after = Pt(0)
        # footer: page number
        fp = sec.footer.paragraphs[0]
        for r in list(fp.runs):
            r._r.getparent().remove(r._r)
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = fp.add_run(); r.font.size = Pt(9); r.font.name = HEAD
        r._r.append(el("w:fldChar", **{"w:fldCharType": "begin"}))
        it = el("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = " PAGE "
        r._r.append(it)
        r._r.append(el("w:fldChar", **{"w:fldCharType": "separate"}))
        t = el("w:t"); t.text = "1"; r._r.append(t)
        r._r.append(el("w:fldChar", **{"w:fldCharType": "end"}))
        sp = sec._sectPr
        for old in sp.findall(qn("w:lnNumType")):
            sp.remove(old)
        if line_numbers:
            ln = el("w:lnNumType", **{"w:countBy": 1, "w:restart": "continuous", "w:distance": 360})
            # schema order: lnNumType goes before pgNumType/cols/docGrid; insert after pgMar
            pgmar = sp.find(qn("w:pgMar"))
            pgmar.addnext(ln)

def add_hyperlink_around(par, run_el, url):
    rid = par.part.relate_to(url, RT.HYPERLINK, is_external=True)
    h = el("w:hyperlink"); h.set(qn("r:id"), rid)
    run_el.addprevious(h); h.append(run_el)
    rpr = run_el.find(qn("w:rPr"))
    if rpr is None:
        rpr = el("w:rPr"); run_el.insert(0, rpr)
    rpr.insert(0, el("w:rStyle", **{"w:val": "Hyperlink"}))

def title_block(d):
    pars = d.paragraphs
    for p in pars:
        if p.style.name != "Author":
            continue
        text = p.text
        # break at ". " before ORCID / Contact (the space becomes a line break; characters unchanged)
        pieces = re.split(r"(?<=\.) (?=ORCID:|Contact:)", text)
        for r in list(p.runs):
            r._r.getparent().remove(r._r)
        for i, piece in enumerate(pieces):
            m = re.match(r"(ORCID: )(\S+?)(\.?)$", piece) or re.match(r"(Contact: )(\S+?@\S+?)(\.?)$", piece)
            if m:
                p.add_run(m.group(1))
                link = p.add_run(m.group(2))
                url = ("https://orcid.org/" + m.group(2)) if piece.startswith("ORCID") else ("mailto:" + m.group(2))
                add_hyperlink_around(p, link._r, url)
                if m.group(3):
                    p.add_run(m.group(3))
            else:
                p.add_run(piece)
            if i < len(pieces) - 1:
                p.add_run().add_break()
        break
    # boxed disclaimer: first body paragraph after Date
    seen_date = False
    for p in pars:
        if p.style.name == "Date":
            seen_date = True; continue
        if seen_date and p.text.strip():
            if p.text.startswith("Educational analysis of public data"):
                ppr = p._p.get_or_add_pPr()
                bdr = el("w:pBdr")
                for side in ("top", "left", "bottom", "right"):
                    bdr.append(el(f"w:{side}", **{"w:val": "single", "w:sz": 6, "w:space": 4, "w:color": "A6A6A6"}))
                ppr.append(bdr)
                ppr.append(el("w:shd", **{"w:val": "clear", "w:color": "auto", "w:fill": "F2F2F2"}))
                p.paragraph_format.left_indent = Inches(0.08); p.paragraph_format.right_indent = Inches(0.08)
                p.paragraph_format.space_after = Pt(12); p.paragraph_format.line_spacing = 1.15
                for r in p.runs:
                    r.font.size = Pt(10)
            break

# ---------- tables ----------
def cell_text(tc):
    return " ".join("".join(t.text or "" for t in p.iter(qn("w:t"))) for p in tc.iter(qn("w:p"))).strip()

def char_w(pt):  # average Calibri char width in twips at size pt (~0.5 em)
    return pt * 20 * 0.5

NUMERIC = re.compile(r"^[\s<>≤≥~+\-−–—()%.,:/0-9a-zA-Z]*$")

def is_numeric(t):
    t = t.strip()
    return t in ("", "—", "–", "-") or bool(re.match(r"^[<>≤≥~+\-−]?[\d.,]+", t)) and len(re.sub(r"[^A-Za-z]", "", t)) <= 3

def size_columns(rows, pt):
    """Header cells may wrap (only their longest word counts); body cells want their full length (capped)."""
    ncol = max(len(r) for r in rows)
    longest_word = [0] * ncol; full = [0] * ncol
    for i, r in enumerate(rows):
        for j, t in enumerate(r):
            words = re.split(r"[\s]+", t) if t else [""]
            lw = max(len(w) for w in words) * (1.15 if i == 0 else 1.0)   # header is bold
            longest_word[j] = max(longest_word[j], lw)
            if i > 0:
                full[j] = max(full[j], len(t))
    pad = 160  # cell margins, twips
    mins = [longest_word[j] * char_w(pt) + pad for j in range(ncol)]
    wants = [min(full[j], 30) * char_w(pt) + pad for j in range(ncol)]
    wants = [max(w, m) for w, m in zip(wants, mins)]
    hdr = rows[0] if rows else []
    nice = [max(wants[j], min(len(hdr[j]) if j < len(hdr) else 0, 16) * char_w(pt) + pad) for j in range(ncol)]
    return mins, wants, nice

def fit_widths(mins, wants, total, nice=None):
    if nice and sum(wants) <= total:
        # first give headers room so they wrap less, then share what is left
        deficit = [n - w for n, w in zip(nice, wants)]
        room = total - sum(wants)
        if sum(deficit) > 0:
            f = min(1.0, room / sum(deficit))
            wants = [w + f * d for w, d in zip(wants, deficit)]
    if sum(wants) <= total:
        extra = total - sum(wants)
        return [w + extra * w / sum(wants) for w in wants], True
    if sum(mins) <= total:
        # shrink toward mins proportionally to slack
        slack = [w - m for w, m in zip(wants, mins)]
        need = sum(wants) - total
        return [w - need * s / sum(slack) for w, s in zip(wants, slack)], True
    return [total * m / sum(mins) for m in mins], False

def rule(tag, sz):
    return el(tag, **{"w:val": "single", "w:sz": sz, "w:space": 0, "w:color": "000000"})

def format_table(tbl):
    trs = tbl.findall(qn("w:tr"))
    rows = [[cell_text(tc) for tc in tr.findall(qn("w:tc"))] for tr in trs]
    ncol = max(len(r) for r in rows)
    pt = 9
    mins, wants, nice = size_columns(rows, pt)
    widths, ok = fit_widths(mins, wants, TEXT_W, nice)
    if not ok or ncol >= 10:
        pt = 8
        mins, wants, nice = size_columns(rows, pt)
        widths, ok = fit_widths(mins, wants, TEXT_W, nice)
    widths = [int(w) for w in widths]
    widths[-1] += TEXT_W - sum(widths)
    tblPr = tbl.find(qn("w:tblPr"))
    for tag in ("w:tblW", "w:tblLayout", "w:tblBorders", "w:tblCellMar", "w:jc"):
        for old in tblPr.findall(qn(tag)):
            tblPr.remove(old)
    style_el = tblPr.find(qn("w:tblStyle"))
    anchor = style_el if style_el is not None else None
    new = [el("w:tblW", **{"w:type": "dxa", "w:w": TEXT_W}), el("w:jc", **{"w:val": "left"})]
    borders = el("w:tblBorders")
    borders.append(rule("w:top", 10)); borders.append(el("w:left", **{"w:val": "nil"}))
    borders.append(rule("w:bottom", 10)); borders.append(el("w:right", **{"w:val": "nil"}))
    borders.append(el("w:insideH", **{"w:val": "nil"})); borders.append(el("w:insideV", **{"w:val": "nil"}))
    new.append(borders)
    new.append(el("w:tblLayout", **{"w:type": "fixed"}))
    mar = el("w:tblCellMar")
    for side, v in (("top", 15), ("left", 70), ("bottom", 15), ("right", 70)):
        mar.append(el(f"w:{side}", **{"w:w": v, "w:type": "dxa"}))
    new.append(mar)
    pos = 1 if anchor is not None else 0
    for i, e in enumerate(new):
        tblPr.insert(pos + i, e)
    grid = tbl.find(qn("w:tblGrid"))
    for g in list(grid):
        grid.remove(g)
    for w in widths:
        grid.append(el("w:gridCol", **{"w:w": w}))
    keep_whole = len(trs) <= KEEP_WHOLE_ROWS   # short tables stay on one page; long ones break with a repeated header
    body_rows = rows[1:] or rows
    numeric_col = [sum(is_numeric(r[j]) for r in body_rows if j < len(r)) >= 0.7 * len(body_rows) for j in range(ncol)]
    for i, tr in enumerate(trs):
        trPr = tr.find(qn("w:trPr"))
        if trPr is None:
            trPr = el("w:trPr"); tr.insert(0, trPr)
        if trPr.find(qn("w:cantSplit")) is None:
            trPr.insert(0, el("w:cantSplit"))
        if i == 0 and trPr.find(qn("w:tblHeader")) is None:
            trPr.append(el("w:tblHeader"))
        for j, tc in enumerate(tr.findall(qn("w:tc"))):
            tcPr = tc.find(qn("w:tcPr"))
            if tcPr is None:
                tcPr = el("w:tcPr"); tc.insert(0, tcPr)
            for old in tcPr.findall(qn("w:tcW")):
                tcPr.remove(old)
            tcPr.insert(0, el("w:tcW", **{"w:type": "dxa", "w:w": widths[j] if j < len(widths) else 0}))
            for old in tcPr.findall(qn("w:tcBorders")):
                tcPr.remove(old)
            if i == 0:
                b = el("w:tcBorders"); b.append(rule("w:bottom", 6)); tcPr.append(b)
                tcPr.append(el("w:vAlign", **{"w:val": "bottom"}))
            for p in tc.findall(qn("w:p")):
                ppr = p.find(qn("w:pPr"))
                if ppr is None:
                    ppr = el("w:pPr"); p.insert(0, ppr)
                for old in ppr.findall(qn("w:spacing")) + ppr.findall(qn("w:jc")):
                    ppr.remove(old)
                ppr.append(el("w:jc", **{"w:val": "right" if (j < ncol and numeric_col[j]) else "left"}))
                ppr.append(el("w:spacing", **{"w:before": 0, "w:after": 0, "w:line": 240, "w:lineRule": "auto"}))
                if keep_whole and i < len(trs) - 1:
                    if ppr.find(qn("w:keepNext")) is None:
                        ppr.insert(1, el("w:keepNext"))
                for r in p.iter(qn("w:r")):
                    rpr = r.find(qn("w:rPr"))
                    if rpr is None:
                        rpr = el("w:rPr"); r.insert(0, rpr)
                    is_code = rpr.find(qn("w:rStyle")) is not None and rpr.find(qn("w:rStyle")).get(qn("w:val")) == "VerbatimChar"
                    if not is_code:
                        set_rfonts(rpr, TABLE)
                    for old in rpr.findall(qn("w:sz")) + rpr.findall(qn("w:szCs")):
                        rpr.remove(old)
                    rpr.append(el("w:sz", **{"w:val": int(pt * 2)})); rpr.append(el("w:szCs", **{"w:val": int(pt * 2)}))
                    if i == 0 and rpr.find(qn("w:b")) is None:
                        rpr.insert(1, el("w:b"))
    return ncol, pt

# ---------- figures ----------
def format_figures(d, max_w=6.0, max_h=4.8):
    for shp in d.inline_shapes:
        w, h = shp.width, shp.height
        if not w or not h:
            continue
        s = min(Inches(max_w) / w, Inches(max_h) / h, 1.0 if w <= Inches(TEXT_W_IN) else 10)
        nw, nh = int(w * s), int(h * s)
        shp.width, shp.height = Emu(nw), Emu(nh)
        # keep the picture's own a:ext in sync
        for ext in shp._inline.iter(qn("a:ext")):
            ext.set("cx", str(nw)); ext.set("cy", str(nh))
    for p in d.paragraphs:
        if p._p.find(".//" + qn("w:drawing")) is not None:
            p.paragraph_format.keep_with_next = True
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

def captions_and_spacing(d):
    """Supplement tables use a bold 'Table S..' paragraph before the table instead of a pandoc caption:
    give it the Table Caption style (kept with its table). Add breathing space after every table."""
    body = d.element.body
    for tbl in body.iter(qn("w:tbl")):
        prev = tbl.getprevious()
        while prev is not None and prev.tag != qn("w:p"):
            prev = prev.getprevious()
        if prev is not None:
            txt = "".join(t.text or "" for t in prev.iter(qn("w:t")))
            if re.match(r"Table S?\d", txt):
                ppr = prev.find(qn("w:pPr"))
                if ppr is None:
                    ppr = el("w:pPr"); prev.insert(0, ppr)
                ps = ppr.find(qn("w:pStyle"))
                if ps is None:
                    ps = el("w:pStyle"); ppr.insert(0, ps)
                ps.set(qn("w:val"), "TableCaption")
        nxt = tbl.getnext()
        while nxt is not None and nxt.tag != qn("w:p") and nxt.tag != qn("w:tbl"):
            nxt = nxt.getnext()
        if nxt is not None and nxt.tag == qn("w:p"):
            ppr = nxt.find(qn("w:pPr"))
            if ppr is None:
                ppr = el("w:pPr"); nxt.insert(0, ppr)
            sp = ppr.find(qn("w:spacing"))
            if sp is None:
                sp = el("w:spacing"); ppr.append(sp)
            sp.set(qn("w:before"), "200")

MINUS_RE = re.compile(r"(?<![\w\-\u2010-\u2015.,/:_)\]])-(?=\d)")

def true_minus(d):
    """Typed hyphen-minus directly before a digit, not preceded by a letter, digit or punctuation that
    makes it a range/hyphen (e.g. 2012-2018, 1-day, 0009-0003), becomes U+2212.
    Skips code (VerbatimChar), hyperlinks and the reference list. Returns the changed contexts."""
    changed = []
    W_P, W_R, W_T = qn("w:p"), qn("w:r"), qn("w:t")
    for p in d.element.body.iter(W_P):
        ps = p.find(qn("w:pPr") + "/" + qn("w:pStyle"))
        if ps is not None and ps.get(qn("w:val")) == "Bibliography":
            continue
        ts = []
        for r in p.iter(W_R):
            if r.getparent().tag == qn("w:hyperlink"):
                skip = True
            else:
                st = r.find(qn("w:rPr") + "/" + qn("w:rStyle"))
                skip = st is not None and st.get(qn("w:val")) == "VerbatimChar"
            for t in r.findall(W_T):
                ts.append((t, skip))
        full = "".join(t.text or "" for t, _ in ts)
        if "-" not in full:
            continue
        owner = []
        for i, (t, skip) in enumerate(ts):
            owner += [(i, j, skip) for j in range(len(t.text or ""))]
        hits = [m.start() for m in MINUS_RE.finditer(full) if not owner[m.start()][2]]
        for pos in hits:
            i, j, _ = owner[pos]
            t = ts[i][0]
            t.text = t.text[:j] + "\u2212" + t.text[j + 1:]
            changed.append(full[max(0, pos - 25):pos + 12])
    return changed

def tighten_bibliography(d, level):
    """level 1-2: slightly tighter reference list, used only to stop the last page holding 1-2 references."""
    s = style(d, "Bibliography")
    if s is None or not level:
        return
    s.paragraph_format.space_after = Pt([3, 1.5, 0.5][min(level, 2)])
    s.paragraph_format.line_spacing = [1.1, 1.05, 1.0][min(level, 2)]

def polish(path_in, path_out, header_text, line_numbers=False, bib_level=0, minus=True):
    d = docx.Document(path_in)
    styles(d)
    tighten_bibliography(d, bib_level)
    page_setup(d, header_text, line_numbers)
    title_block(d)
    report = []
    for t in d.element.body.iter(qn("w:tbl")):
        report.append(format_table(t))
    format_figures(d)
    captions_and_spacing(d)
    changed = true_minus(d) if minus else []
    d.save(path_out)
    return {"tables": report, "minus": changed}

if __name__ == "__main__":
    a = sys.argv[1:]
    ln = "--line-numbers" in a
    a = [x for x in a if x != "--line-numbers"]
    print(polish(a[0], a[1], "Educational analysis of public data. Not clinical or ordering advice.", ln))
