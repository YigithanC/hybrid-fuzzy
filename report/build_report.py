"""Build the technical report (Turkish) as report/report.docx.

All result numbers in tables, and the key numbers quoted in the text, are read
from results/tables/*.csv, so the report always matches the experiments.
Citations are written as [@key] and renumbered in order of first appearance (IEEE).

    python report/build_report.py            # -> report/report.docx
    powershell -File report/export_pdf.ps1   # -> report/report.pdf (needs MS Word)
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures"
TAB = ROOT / "results" / "tables"
OUT = ROOT / "report" / "report.docx"

FONT = "Times New Roman"
TEXT_W = Cm(16.0)

# ----------------------------------------------------------------------------------------------
# References (IEEE). Verified against Crossref, see references/README.md
# ----------------------------------------------------------------------------------------------
REFS = {
    "melhaoui": 'M. Melhaoui, M. Rhiat, M. Oukili, I. Atmane, K. Hirech, B. Bossoufi, M. M. Almalki, T. A. H. Alghamdi, and M. Alenezi, "Hybrid fuzzy logic approach for enhanced MPPT control in PV systems," Sci. Rep., vol. 15, no. 1, Art. no. 19235, 2025, doi: 10.1038/s41598-025-03154-w.',
    "zadeh": 'L. A. Zadeh, "Fuzzy sets," Inf. Control, vol. 8, no. 3, pp. 338–353, 1965, doi: 10.1016/S0019-9958(65)90241-X.',
    "mamdani": 'E. H. Mamdani and S. Assilian, "An experiment in linguistic synthesis with a fuzzy logic controller," Int. J. Man-Mach. Stud., vol. 7, no. 1, pp. 1–13, 1975, doi: 10.1016/S0020-7373(75)80002-2.',
    "esram": 'T. Esram and P. L. Chapman, "Comparison of photovoltaic array maximum power point tracking techniques," IEEE Trans. Energy Convers., vol. 22, no. 2, pp. 439–449, 2007, doi: 10.1109/TEC.2006.874230.',
    "bhatnagar": 'P. Bhatnagar and R. K. Nema, "Maximum power point tracking control techniques: State-of-the-art in photovoltaic applications," Renew. Sustain. Energy Rev., vol. 23, pp. 224–241, 2013, doi: 10.1016/j.rser.2013.02.011.',
    "bollipo": 'R. B. Bollipo, S. Mikkili, and P. K. Bonthagorla, "Hybrid, optimization, intelligent and classical PV MPPT techniques: Review," CSEE J. Power Energy Syst., vol. 7, no. 1, pp. 9–33, 2020, doi: 10.17775/CSEEJPES.2019.02720.',
    "vidal": 'R. Vidal-Martínez, J. R. García-Martínez, R. Rojas-Galván, J. M. Álvarez-Alvarado, M. Gozález-Lee, and J. Rodríguez-Reséndiz, "A review of Mamdani, Takagi–Sugeno, and Type-2 fuzzy controllers for MPPT and power management in photovoltaic systems," Technologies, vol. 13, no. 9, Art. no. 422, 2025, doi: 10.3390/technologies13090422.',
    "femia": 'N. Femia, G. Petrone, G. Spagnuolo, and M. Vitelli, "Optimization of perturb and observe maximum power point tracking method," IEEE Trans. Power Electron., vol. 20, no. 4, pp. 963–973, 2005, doi: 10.1109/TPEL.2005.850975.',
    "elgendy12": 'M. A. Elgendy, B. Zahawi, and D. J. Atkinson, "Assessment of perturb and observe MPPT algorithm implementation techniques for PV pumping applications," IEEE Trans. Sustain. Energy, vol. 3, no. 1, pp. 21–33, 2012, doi: 10.1109/TSTE.2011.2168245.',
    "elgendy13": 'M. A. Elgendy, B. Zahawi, and D. J. Atkinson, "Assessment of the incremental conductance maximum power point tracking algorithm," IEEE Trans. Sustain. Energy, vol. 4, no. 1, pp. 108–117, 2013, doi: 10.1109/TSTE.2012.2202698.',
    "loukriz": 'A. Loukriz, M. Haddadi, and S. Messalti, "Simulation and experimental design of a new advanced variable step size incremental conductance MPPT algorithm for PV systems," ISA Trans., vol. 62, pp. 30–38, 2016, doi: 10.1016/j.isatra.2015.08.006.',
    "djilali": 'A. B. Djilali et al., "Enhanced variable step sizes perturb and observe MPPT control to reduce energy loss in photovoltaic systems," Sci. Rep., vol. 15, no. 1, Art. no. 11700, 2025, doi: 10.1038/s41598-025-95309-y.',
    "shiau": 'J.-K. Shiau, Y.-C. Wei, and B.-C. Chen, "A study on the fuzzy-logic-based solar power MPPT algorithms using different fuzzy input variables," Algorithms, vol. 8, no. 2, pp. 100–127, 2015, doi: 10.3390/a8020100.',
    "robles": 'C. Robles Algarín, J. Taborda Giraldo, and O. Rodríguez Álvarez, "Fuzzy logic based MPPT controller for a PV system," Energies, vol. 10, no. 12, Art. no. 2036, 2017, doi: 10.3390/en10122036.',
    "yilmaz": 'U. Yilmaz, A. Kircay, and S. Borekci, "PV system fuzzy logic MPPT method and PI control as a charge controller," Renew. Sustain. Energy Rev., vol. 81, pp. 994–1001, 2018, doi: 10.1016/j.rser.2017.08.048.',
    "ali": 'Z. M. Ali et al., "Novel hybrid improved bat algorithm and fuzzy system based MPPT for photovoltaic under variable atmospheric conditions," Sustain. Energy Technol. Assess., vol. 52, Art. no. 102156, 2022, doi: 10.1016/j.seta.2022.102156.',
    "priyadarshi": 'N. Priyadarshi, S. Padmanaban, J. B. Holm-Nielsen, F. Blaabjerg, and M. S. Bhaskar, "An experimental estimation of hybrid ANFIS–PSO-based MPPT for PV grid integration under fluctuating sun irradiance," IEEE Syst. J., vol. 14, no. 1, pp. 1218–1229, 2020, doi: 10.1109/JSYST.2019.2949083.',
    "altin": 'N. Altin, "Interval type-2 fuzzy logic controller based maximum power point tracking in photovoltaic systems," Adv. Electr. Comput. Eng., vol. 13, no. 3, pp. 65–70, 2013, doi: 10.4316/AECE.2013.03011.',
    "boudia": 'A. Boudia, S. Messalti, S. Zeghlache, and A. Harrag, "Type-2 fuzzy logic controller-based maximum power point tracking for photovoltaic system," Electr. Eng. Electromech., no. 1, pp. 16–22, 2025, doi: 10.20998/2074-272X.2025.1.03.',
    "intravaia": 'M. Intravaia et al., "Sensitivity analysis of PV produced power in presence of measurement uncertainty," in Proc. IEEE Int. Workshop Metrol. Ind. 4.0 IoT (MetroInd4.0&IoT), 2024, pp. 245–250, doi: 10.1109/MetroInd4.0IoT61288.2024.10584219.',
    "villalva": 'M. G. Villalva, J. R. Gazoli, and E. Ruppert Filho, "Comprehensive approach to modeling and simulation of photovoltaic arrays," IEEE Trans. Power Electron., vol. 24, no. 5, pp. 1198–1208, 2009, doi: 10.1109/TPEL.2009.2013862.',
    "numpy": 'C. R. Harris et al., "Array programming with NumPy," Nature, vol. 585, no. 7825, pp. 357–362, 2020, doi: 10.1038/s41586-020-2649-2.',
    "scipy": 'P. Virtanen et al., "SciPy 1.0: Fundamental algorithms for scientific computing in Python," Nat. Methods, vol. 17, no. 3, pp. 261–272, 2020, doi: 10.1038/s41592-019-0686-2.',
}
_order: list[str] = []


def cite(text: str) -> str:
    """Replace [@a] / [@a,@b] markers by IEEE numbers in order of first appearance."""
    def repl(m):
        nums = []
        for key in re.findall(r"@([\w]+)", m.group(0)):
            if key not in REFS:
                raise KeyError(key)
            if key not in _order:
                _order.append(key)
            nums.append(_order.index(key) + 1)
        return "[" + "], [".join(str(n) for n in nums) + "]"
    return re.sub(r"\[@[^\]]+\]", repl, text)


# ----------------------------------------------------------------------------------------------
# Numbers from the experiment outputs
# ----------------------------------------------------------------------------------------------
t6 = pd.read_csv(TAB / "table6_reproduction.csv")
t7 = pd.read_csv(TAB / "table7_reproduction.csv")
ns = pd.read_csv(TAB / "noise_summary_extension.csv")
f13 = pd.read_csv(TAB / "fig13_sinc_csi_ranges.csv")
row6 = {r["algorithm"]: r for _, r in t6.iterrows()}
P6 = row6["Proposed (SInC+CSI)"]


def eff(variant: str, level: float) -> float:
    return float(ns[(ns.variant == variant) & (ns.noise_pct_fs == level)].efficiency_mean.iloc[0])


def effstd(variant: str, level: float) -> float:
    return float(ns[(ns.variant == variant) & (ns.noise_pct_fs == level)].efficiency_std.iloc[0])


def conv0(variant: str) -> float:
    return float(ns[(ns.variant == variant) & (ns.noise_pct_fs == 0.0)].conv_avg_ms_mean.iloc[0])


def f(x: float, d: int = 2) -> str:
    """Turkish decimal comma and a typographic minus sign."""
    return f"{x:.{d}f}".replace(".", ",").replace("-", "−")


ALGO_TR = {"P&O": "P&O", "InC": "InC", "Alg. 3 (SInC)": "Alg. 3 (SInC)",
           "Proposed (SInC+CSI)": "Önerilen (SInC+CSI)"}


N = {
    "eff_prop": f(P6.efficiency_pct), "conv_prop": f(P6.conv_avg_ms, 1), "rmse_prop": f(P6.rmse_w),
    "eff_alg3": f(row6["Alg. 3 (SInC)"].efficiency_pct), "eff_po": f(row6["P&O"].efficiency_pct),
    "eff_inc": f(row6["InC"].efficiency_pct),
    "n0": f(eff("flc_sinc_csi", 0.0)), "n05": f(eff("flc_sinc_csi", 0.5)), "n1": f(eff("flc_sinc_csi", 1.0)),
    "r0": f(eff("prop+FDC", 0.0)), "r05": f(eff("prop+FDC", 0.5)), "r1": f(eff("prop+FDC", 1.0)),
    "r1s": f(effstd("prop+FDC", 1.0)), "n1s": f(effstd("flc_sinc_csi", 1.0)),
    "a3r1": f(eff("alg3+FDC", 1.0)), "a31": f(eff("flc_sinc", 1.0)),
    "F1": f(eff("prop+F", 1.0)), "D1": f(eff("prop+D", 1.0)), "C1": f(eff("prop+C", 1.0)),
    "po1": f(eff("po", 1.0)), "po05": f(eff("po", 0.5)), "poF05": f(eff("po+F", 0.5)),
    "g1": f(eff("prop+FDC+gauss", 1.0)), "g1s": f(effstd("prop+FDC+gauss", 1.0)),
    "conv_r": f(conv0("prop+FDC"), 1),
    "t7_1000": f(t7[(t7.G == 1000) & (t7.algorithm.str.startswith("Proposed"))].rmse_w.iloc[0]),
}

# ----------------------------------------------------------------------------------------------
# docx helpers
# ----------------------------------------------------------------------------------------------
doc = Document()
_fig = [0]
_tab = [0]
_eq = [0]


def setup() -> None:
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Cm(2.5))
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    pf = st.paragraph_format
    pf.space_after = Pt(4)
    pf.line_spacing = 1.08
    for lvl, size in ((1, 13), (2, 11.5), (3, 11)):
        h = doc.styles[f"Heading {lvl}"]
        h.font.name = FONT
        h.font.size = Pt(size)
        h.font.bold = True
        h.font.italic = lvl == 3
        h.font.color.rgb = RGBColor(0, 0, 0)
        h.element.rPr.rFonts.set(qn("w:asciiTheme"), "")
        h.element.rPr.rFonts.set(qn("w:ascii"), FONT)
        h.element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
        h.paragraph_format.space_before = Pt(10 if lvl == 1 else 6)
        h.paragraph_format.space_after = Pt(3)
        h.paragraph_format.keep_with_next = True
    # page number in footer
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)


def para(text: str, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size: float | None = None, bold=False, italic=False,
         space_after: float | None = None, indent: bool = False):
    p = doc.add_paragraph()
    p.alignment = align
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.6)
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    _runs(p, cite(text), size, bold, italic)
    return p


_SUB = re.compile(r"(?<=[A-Za-zΔδσμηξ0-9)\]])_([A-Za-z0-9]+)")


def _runs(p, text: str, size=None, bold=False, italic=False):
    """Inline markup: **bold**, *italic*, `code`, and X_sub -> X with a real subscript."""
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)", text):
        if not part:
            continue
        b, i, t, code = bold, italic, part, False
        if part.startswith("**"):
            b, t = True, part[2:-2]
        elif part.startswith("`"):
            code, t = True, part[1:-1]
        elif part.startswith("*"):
            i, t = True, part[1:-1]
        pieces = [(t, False)] if code else []
        if not code:
            pos = 0
            for m in _SUB.finditer(t):
                pieces.append((t[pos:m.start()], False))
                pieces.append((m.group(1), True))
                pos = m.end()
            pieces.append((t[pos:], False))
        for txt, sub in pieces:
            if not txt:
                continue
            r = p.add_run(txt)
            r.bold, r.italic = b, i
            r.font.subscript = sub
            if code:
                r.font.name = "Consolas"
            if size:
                r.font.size = Pt(size - (1 if code else 0))


def bullets(items: list[str]) -> None:
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(2)
        _runs(p, cite(it))


def h(text: str, lvl: int = 1) -> None:
    doc.add_heading(text, level=lvl)


def eq(*lines: str) -> int:
    """Centered equation (one or more lines) with the number right-aligned on the last line."""
    _eq[0] += 1
    for k, text in enumerate(lines):
        last = k == len(lines) - 1
        p = doc.add_paragraph()
        ts = p.paragraph_format.tab_stops
        ts.add_tab_stop(Cm(8.0), WD_TAB_ALIGNMENT.CENTER)
        ts.add_tab_stop(TEXT_W, WD_TAB_ALIGNMENT.RIGHT)
        p.paragraph_format.space_before = Pt(2 if k == 0 else 0)
        p.paragraph_format.space_after = Pt(4 if last else 0)
        p.paragraph_format.keep_with_next = not last
        p.add_run("\t")
        _runs(p, text, italic=True)
        p.add_run("\t" + (f"({_eq[0]})" if last else ""))
    return _eq[0]


def figure(name: str, caption: str, width_cm: float = 15.5) -> int:
    _fig[0] += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(FIG / name), width=Cm(width_cm))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(8)
    r = c.add_run(f"Şekil {_fig[0]}. ")
    r.bold = True
    r.font.size = Pt(9)
    _runs(c, cite(caption), size=9)
    return _fig[0]


def table(header: list[str], rows: list[list[str]], caption: str, widths_cm: list[float],
          font_size: float = 9, bold_rows: tuple[int, ...] = ()) -> int:
    _tab[0] += 1
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.keep_with_next = True
    c.paragraph_format.space_after = Pt(2)
    r = c.add_run(f"Tablo {_tab[0]}. ")
    r.bold = True
    r.font.size = Pt(9)
    _runs(c, cite(caption), size=9)
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, w in enumerate(widths_cm):
        for row in t.rows:
            row.cells[j].width = Cm(w)
    for j, txt in enumerate(header):
        cell = t.rows[0].cells[j]
        cell.text = ""
        _runs(cell.paragraphs[0], cite(txt), size=font_size, bold=True)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:fill"), "E7ECF3")
        cell._tc.get_or_add_tcPr().append(shd)
    for i, row in enumerate(rows, start=1):
        for j, txt in enumerate(row):
            cell = t.rows[i].cells[j]
            cell.text = ""
            _runs(cell.paragraphs[0], cite(str(txt)), size=font_size, bold=(i - 1) in bold_rows)
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in t.rows:
        row.cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return _tab[0]


# ----------------------------------------------------------------------------------------------
# Content
# ----------------------------------------------------------------------------------------------
def title_block() -> None:
    para("Hibrit InC–Bulanık Mantık MPPT Denetleyicisinin Yeniden Üretimi ve Ölçüm Gürültüsüne Dayanıklı "
         "SInC Kestiricisi ile Geliştirilmesi", WD_ALIGN_PARAGRAPH.CENTER, size=15, bold=True, space_after=6)
    para("Yiğithan Çalışkan (1306230049)", WD_ALIGN_PARAGRAPH.CENTER, size=11, space_after=0)
    para("Bulanık Mantık Dersi – Dönem Projesi Teknik Raporu · Kasım 2026", WD_ALIGN_PARAGRAPH.CENTER, size=10,
         space_after=0)
    para("Kod ve veriler: https://github.com/YigithanC/hybrid-fuzzy", WD_ALIGN_PARAGRAPH.CENTER, size=10,
         space_after=10)
    p = para(
        "**Özet—** Bu çalışmada Melhaoui vd. [@melhaoui] tarafından önerilen, artımsal iletkenlik (InC) ile Mamdani "
        "tipi bulanık mantığı birleştiren maksimum güç noktası izleme (MPPT) denetleyicisi incelenmiş, Python ortamında "
        "sıfırdan yeniden üretilmiş ve ölçüm gürültüsüne karşı geliştirilmiştir. Denetleyici, iletkenlik ile artımsal "
        "iletkenliğin toplamı (SInC) ve bunun değişimi (CSI) olmak üzere iki bulanık girdi kullanır. SunPower SPR-210 "
        "paneli için tek diyotlu bir model ve ortalama durum-uzayı boost dönüştürücü modeli kurulmuş; makaledeki "
        f"ışınım basamağı deneyinde önerilen denetleyici %{N['eff_prop']} ortalama verim ve {N['conv_prop']} ms ortalama "
        "yakınsama süresi ile makaledeki sıralamayı (önerilen > tek girdili SInC > InC ≈ P&O) doğrulamıştır. Makalenin "
        "kendi sınırlılık olarak belirttiği ancak test etmediği ölçüm duyarlılığı nicel olarak incelenmiş; tam ölçeğin "
        f"%1'i düzeyindeki Gauss gürültüsünde verimin %{N['n1']} düzeyine düştüğü ve bunun nedeninin gürültü altında SInC'nin "
        "sistematik olarak pozitif yönde sapması olduğu gösterilmiştir. Önerilen dayanıklı SInC kestiricisi (üstel "
        "hareketli ortalama filtresi ve birikimli fark ölü bölgesi), bulanık kural tabanını değiştirmeden aynı koşulda "
        f"verimi %{N['r1']} düzeyine çıkarmıştır; bedeli gürültüsüz durumda {f(P6.efficiency_pct - eff('prop+FDC', 0.0))} "
        "puanlık verim kaybı ve daha uzun yakınsama süresidir.", size=10)
    para("**Anahtar kelimeler—** Bulanık mantık, Mamdani çıkarımı, MPPT, artımsal iletkenlik, fotovoltaik sistem, "
         "ölçüm gürültüsü, yeniden üretilebilirlik.", size=10, space_after=8)


def s1() -> None:
    h("1. Giriş (Introduction)")
    para("Fotovoltaik (PV) panelin akım–gerilim karakteristiği doğrusal değildir ve çıkış gücü yalnızca tek bir "
         "çalışma noktasında, maksimum güç noktasında (MPP), en büyük değerini alır. MPP ışınım ve sıcaklıkla sürekli "
         "yer değiştirdiği için panel ile yük arasına bir DC–DC dönüştürücü yerleştirilir ve görev oranı (D) bir MPPT "
         "algoritmasıyla ayarlanır [@esram,@bhatnagar]. En yaygın yöntemler olan Değiştir-Gözle (P&O) ve artımsal "
         "iletkenlik (InC) basit olmakla birlikte sabit adım kullanır; büyük adım hızlı ama salınımlı, küçük adım "
         "kararlı ama yavaş bir izleme verir [@femia,@elgendy13]. Bulanık mantık denetleyicileri (FLC) ise adım "
         "büyüklüğünü çalışma noktasının MPP'ye uzaklığına göre dilsel kurallarla uyarlar ve kesin bir matematiksel "
         "model gerektirmez [@shiau,@robles].", indent=True)
    para("Referans makale [@melhaoui], InC koşulunu bulanık denetleyiciye taşıyan dört hibrit FLC'yi karşılaştırır ve "
         "SInC ile CSI girdilerini kullanan yeni bir denetleyici önerir. Makale, MATLAB/Simulink benzetiminde %97,7 "
         "ortalama verim ve 53,5 ms yakınsama süresi raporlar; ancak sonuç bölümünde yöntemin ölçüm hassasiyetine ve "
         "bölme işlemine duyarlı olduğunu belirtir ve bu duyarlılığı test etmez. Bu proje bu boşluktan hareket eder.",
         indent=True)
    para("Projenin kapsamı ve katkıları şunlardır:")
    bullets([
        "Referans makalenin problem, yöntem, deney ve sınırlılıklarının incelenmesi ve güncel literatürle "
        "konumlandırılması (Bölüm 2–4).",
        "Minimum yeniden üretim gereksinimi olarak PV paneli, boost dönüştürücü ve önerilen SInC+CSI bulanık "
        "denetleyicinin Python'da sıfırdan gerçekleştirilmesi; makaledeki ışınım basamağı (Tablo 6) ve yük "
        "basamağı (Tablo 7) deneylerinin yeniden üretilmesi (Bölüm 5, 8).",
        "Özgün katkı: denetleyicinin ölçüm gürültüsüne duyarlılığının nicel analizi, duyarlılığın mekanizmasının "
        "açıklanması ve ablasyon çalışmasıyla değerlendirilen dayanıklı bir SInC kestiricisi (Bölüm 6, 8).",
        "Tüm kod, veri ve şekillerin tek komutla yeniden üretilebilir biçimde GitHub'da paylaşılması.",
    ])


def s2() -> None:
    h("2. İlgili Çalışmalar (Related Work)")
    para("**Klasik MPPT.** Esram ve Chapman [@esram] ile Bhatnagar ve Nema [@bhatnagar] MPPT yöntemlerini kapsamlı "
         "biçimde karşılaştırır; Bollipo vd. [@bollipo] yöntemleri klasik, akıllı, optimizasyon tabanlı ve hibrit "
         "olarak sınıflandırır ve kısmi gölgelenmede çok tepeli P–V eğrisinde klasik yöntemlerin global tepeyi "
         "kaçırdığını vurgular. Femia vd. [@femia] P&O'nun adım ve örnekleme periyodunun dönüştürücü dinamiğine göre "
         "seçilmesi gerektiğini gösterir; Elgendy vd. P&O [@elgendy12] ve InC [@elgendy13] için uygulama seçeneklerini "
         "(referans gerilim veya doğrudan görev oranı kontrolü, adım ve örnekleme hızı) değerlendirir. Değişken adımlı "
         "InC [@loukriz] ve P&O [@djilali] adımı çalışma noktasına göre ayarlayarak hız–salınım ödünleşimini azaltır; "
         "[@djilali] güç dalgalanmasında %80 azalma raporlar.", indent=True)
    para("**Bulanık MPPT.** Shiau vd. [@shiau] farklı girdilere sahip altı bulanık MPPT algoritmasını karşılaştırır ve "
         "bunlardan biri iletkenlik ile artımsal iletkenliğin toplamını (SInC) tek bulanık girdi olarak kullanır. "
         "Dolayısıyla SInC girdisi referans makaleden önce önerilmiştir; [@melhaoui]'in özgün katkısı ikinci girdi "
         "olarak CSI'yı eklemek ve kural tabanını düşük ışınım için genişletmektir. Robles Algarín vd. [@robles] bulanık "
         "MPPT'nin P&O'ya göre oturma süresi, güç kaybı ve salınım açısından üstün olduğunu, Yilmaz vd. [@yilmaz] "
         "bulanık MPPT'nin PI tabanlı şarj denetimiyle birlikte kullanılabileceğini gösterir. Metasezgisel ve "
         "nöro-bulanık hibritler [@ali,@priyadarshi] ile aralık Type-2 [@altin] ve Type-2 [@boudia] bulanık "
         "denetleyiciler de önerilmiştir. Vidal-Martínez vd. [@vidal] son on yıldaki bulanık PV denetleyicilerinin "
         "%54,2'sinin Mamdani, %26,7'sinin Takagi–Sugeno, %19,1'inin Type-2 olduğunu ve Type-2 yapıların sensör "
         "gürültüsüne karşı tercih edildiğini belirtir.", indent=True)
    para("**Ölçüm belirsizliği.** Intravaia vd. [@intravaia] P&O, InC ve yapay sinir ağı izleyicilerinin ölçüm "
         "gürültüsüne duyarlılığını karşılaştırır ve belirsizlik altında sinir ağının daha dayanıklı olduğunu bulur. "
         "Bu çalışma ise SInC+CSI tabanlı bulanık denetleyicinin gürültü duyarlılığını ölçer ve kural tabanını veya "
         "çıkarım tipini değiştirmeden, yalnızca girdi kestirimini iyileştirerek dayanıklılık sağlar. Tablo 1 seçilmiş "
         "çalışmaları özetler.", indent=True)
    table(["Çalışma", "Yöntem", "Bulanık girdi / ana fikir", "Doğrulama", "Raporlanan sonuç"], [
        ["Shiau vd. [@shiau], 2015", "6 bulanık MPPT", "Eğim, ΔP, ΔV, SInC (tek girdi)", "Benzetim", "Girdilerin artı/eksileri"],
        ["Robles Algarín vd. [@robles], 2017", "Mamdani FLC", "–", "Simulink, 65 W", "P&O'dan hızlı, az salınımlı"],
        ["Priyadarshi vd. [@priyadarshi], 2020", "ANFIS + PSO", "Nöro-bulanık", "dSPACE deney", "P&O, PSO, ACO, ABC'den üstün"],
        ["Boudia vd. [@boudia], 2025", "Type-2 FLC", "Dinamik referans gerilim hatası", "Benzetim", "Type-1'den hızlı, az salınımlı"],
        ["Intravaia vd. [@intravaia], 2024", "Gürültü analizi", "P&O, InC, YSA", "Benzetim", "Belirsizlikte YSA en dayanıklı"],
        ["Melhaoui vd. [@melhaoui], 2025", "InC + Mamdani", "SInC + CSI", "Simulink, SPR-210", "%97,7 verim, 53,5 ms"],
        ["Bu çalışma", "[@melhaoui] + dayanıklı kestirici", "SInC + CSI, EMA + ölü bölge", "Python",
         f"%{N['r1']} verim (%1 gürültü)"],
    ], "Seçilmiş ilgili çalışmaların karşılaştırması.", [3.4, 2.6, 3.6, 2.4, 4.0], font_size=8, bold_rows=(6,))


def s3() -> None:
    h("3. Kuramsal Altyapı (Theoretical Background)")
    h("3.1 Bulanık kümeler, dilsel değişkenler ve üyelik fonksiyonları", 2)
    para("Zadeh'in bulanık küme kuramında [@zadeh] bir x elemanının A kümesine aitliği 0 ile 1 arasında bir üyelik "
         "derecesi μA(x) ile ifade edilir. Dilsel değişkenler sayısal bir büyüklüğü \"Negatif Büyük (NB)\", "
         "\"Sıfır (ZE)\", \"Pozitif Küçük (PS)\" gibi etiketlerle tanımlar ve her etikete bir üyelik fonksiyonu (ÜF) "
         "karşılık gelir. Bu çalışmada üçgen ÜF'ler kullanılır; komşu üçgenler birbirinin tepe noktasında sıfırlanır, "
         "böylece her x için üyeliklerin toplamı 1 olur (Ruspini bölüntüsü) ve uçtaki kümeler omuz (yamuk) biçimindedir. "
         "Bulanıklaştırma, ölçülen keskin değerin bu kümelerdeki üyelik derecelerinin hesaplanmasıdır.", indent=True)
    h("3.2 Mamdani çıkarımı ve durulaştırma", 2)
    para("Mamdani denetleyicisinde [@mamdani] kurallar \"EĞER SInC A ise VE CSI B ise O HALDE ΔD C'dir\" "
         "biçimindedir. VE işleci minimum ile, kuralların birleştirilmesi maksimum ile, çıkış kümesinin kural gücüyle "
         "kırpılması minimum ile yapılır ve sonuç ağırlık merkezi (centroid) yöntemiyle keskin bir değere çevrilir:")
    eq("w_r = min( μ_Ar(SInC), μ_Br(CSI) ),     μ_out(u) = max_r min( w_r, μ_Cr(u) )")
    eq("ΔD = Σ_u u · μ_out(u)  /  Σ_u μ_out(u)")
    para("Takagi–Sugeno denetleyicileri sonuç kısmında doğrusal fonksiyonlar kullanarak durulaştırma adımını kaldırır; "
         "Type-2 denetleyiciler ise üyelik derecesinin kendisini bulanık kabul eden bir belirsizlik ayak izi (FOU) ile "
         "gürültüye karşı ek dayanıklılık hedefler [@vidal]. Referans makale Mamdani yapısını kullandığı için bu "
         "çalışma da Mamdani ile sınırlıdır.", indent=True)
    h("3.3 PV paneli ve MPP koşulu", 2)
    para("Panel, tek diyotlu eşdeğer devre ile modellenir [@villalva]:")
    eq("I = I_ph − I_0 [ exp( (V + I·R_s) / (n·N_s·V_T) ) − 1 ] − (V + I·R_s) / R_sh")
    para("Burada I_ph ışınımla doğrusal değişen foton akımı, I_0 diyot doyma akımı, R_s ve R_sh seri ve paralel "
         "dirençler, n idealite faktörü, N_s seri hücre sayısı ve V_T ısıl gerilimdir. MPP'de dP/dV = 0'dır. P = V·I "
         "olduğundan bu koşul, InC algoritmasının temelini oluşturan biçime dönüşür:")
    eq("dP/dV = I + V·dI/dV = 0   ⇔   SInC ≡ I/V + dI/dV = 0")
    para("SInC < 0 iken çalışma noktası MPP'nin sağında (gerilim fazla), SInC > 0 iken solundadır. Boost dönüştürücüde "
         "panelin gördüğü direnç R_in = R(1 − D)² olduğundan, D'yi artırmak panel gerilimini düşürür; bu nedenle "
         "SInC < 0 iken D artırılır, SInC > 0 iken azaltılır.", indent=True)


def s4() -> None:
    h("4. Referans Yöntem (Original Method)")
    para("Referans sistem bir SunPower SPR-210 paneli (V_oc = 47,8 V, I_sc = 5,65 A, V_mp = 40 V, I_mp = 5,25 A, "
         "P_max = 210 W), 10 kHz PWM ile sürülen bir boost dönüştürücü ve 50 Ω'luk dirençli yükten oluşur. Dönüştürücü "
         "STC'de R_mpp = 7,62 Ω ve D_mpp = 0,61 için tasarlanmış; %4 akım ve %0,5 gerilim dalgalanması için "
         "L = 12 mH, C_o = 250 µF ve ξ = 0,7 sönüm oranı için C_e = 150 µF seçilmiştir [@melhaoui]. Makale aynı ΔD "
         "çıkışını paylaşan dört hibrit FLC'yi karşılaştırır: (1) P–V eğimi ve ΔP, (2) eğim ve eğimin değişimi, "
         "(3) yalnızca SInC ve (4) önerilen SInC + CSI. Önerilen denetleyicide her MPPT adımında")
    eq("SInC[k] = I[k]/V[k] + (I[k] − I[k−1]) / (V[k] − V[k−1]),     CSI[k] = SInC[k] − SInC[k−1]")
    para("hesaplanır, Mamdani çıkarımıyla ΔD bulunur ve D[k+1] = D[k] + ΔD uygulanır. SInC yedi (NB…PB), CSI beş "
         "(NB, NS, ZE, PS, PB) dilsel değere sahiptir; 35 kurallık taban Tablo 2'de verilmiştir. Kural tabanı tek "
         "girdili denetleyiciye göre iki noktada farklılaşır: SInC NS iken CSI büyükse aşmayı önlemek için ΔD = ZE "
         "seçilir; düşük ışınımda MPP'nin solunda kalındığında (SInC PS veya PM, CSI ZE) adım NM ve NB'ye "
         "büyütülür. Makale ÜF'lerin sayısal sınırlarını vermez.", indent=True)
    from src.fuzzy_rules import RULES_PROPOSED, SINC_LABELS
    rows = [[f"CSI = {c}"] + [RULES_PROPOSED[c][s] for s in SINC_LABELS] for c in RULES_PROPOSED]
    table(["", *[f"SInC {s}" for s in SINC_LABELS]], rows,
          "Önerilen denetleyicinin kural tabanı (ΔD çıkışı), [@melhaoui] Tablo 5.", [2.4] + [1.9] * 7, font_size=8.5)
    para("Deneyler 25 °C'de iki senaryoda yapılmıştır: (i) 0,2 s aralıklarla 200, 600, 800, 400, 1000, 1000, 400, 800, "
         "600, 200 W/m² ışınım basamakları (2 s) ve (ii) sabit 1000 ve 500 W/m² altında yükün 0,2 s'de 50'den 20 Ω'a, "
         "0,4 s'de 35 Ω'a değiştirilmesi. Başarım ortalama MPPT verimi η = ΣP_pv / ΣP_opt, yakınsama süresi, RMSE ve "
         "normalize RMS ile ölçülmüştür. Makale önerilen denetleyici için %97,7 verim, 53,5 ms yakınsama ve 8,6 W RMSE "
         "raporlar.", indent=True)


def s5() -> None:
    h("5. Yeniden Üretim Yöntemi (Reproduction Methodology)")
    para("Makalenin yazarları kodlarını paylaşmamıştır; tüm sistem bu proje kapsamında Python'da sıfırdan "
         "yazılmıştır (Şekil 1). Kaynak kod `src/` klasöründe, deney betikleri `experiments/` klasöründedir.", indent=True)
    figure("system_diagram.png", "Yeniden üretilen sistemin blok diyagramı.", 15.0)
    h("5.1 PV modeli", 2)
    para("Denklem (3)'teki dört bilinmeyen (I_ph, I_0, R_s, R_sh), n = 1 sabitlenerek dört koşuldan çözülmüştür: "
         "I(0) = I_sc, I(V_oc) = 0, I(V_mp) = I_mp ve MPP'de dI/dV = −I_mp/V_mp (SciPy fsolve [@scipy]). Sonuçta "
         "R_s = 0,397 Ω ve R_sh = 264 Ω bulunmuş; model STC'de 210,0 W ve R_mpp = 7,62 Ω vererek makaledeki değerleri "
         "birebir sağlamıştır (Şekil 2). I(V) denklemi her adımda Newton yinelemesiyle çözülür.", indent=True)
    figure("pv_curves.png", "SPR-210 modelinin farklı ışınımlarda I–V ve P–V eğrileri (25 °C).", 13.5)
    h("5.2 Boost dönüştürücü modeli", 2)
    para("Anahtarlamalı Simulink modeli yerine, bir anahtarlama periyodu üzerinden ortalanmış durum-uzayı modeli "
         "kullanılmıştır. Bu model L–C_e rezonansı ve çıkış RC'si gibi yakınsama süresini belirleyen düşük frekanslı "
         "dinamikleri korur, 10 kHz dalgalanmayı ise ihmal eder:")
    eq("C_e · dv_pv/dt = i_pv − i_L", "L · di_L/dt = v_pv − (1 − D) · v_o", "C_o · dv_o/dt = (1 − D) · i_L − v_o / R")
    para("Denklemler 10 µs adımlı ileri Euler yöntemiyle çözülür; diyot ters akımı engellediği için i_L ≥ 0 "
         "sınırlanır. MPPT denetleyicisi V ve I'yı her T_s = 1 ms'de örnekler. Makale MPPT periyodunu vermediği için "
         "1 ms, açık çevrim taramasında makaledekiyle aynı mertebede CSI değerleri verdiği için seçilmiştir "
         "(Bölüm 8.1).", indent=True)
    h("5.3 Bulanık çıkarım motoru ve üyelik fonksiyonları", 2)
    para("Mamdani çıkarımı (min–max, centroid; Denklem 1–2) savunmada her adımı açıklanabilsin diye proje içinde "
         "yazılmış, ÜF şekilleri ve centroid hesabı scikit-fuzzy kütüphanesinden alınmıştır. Makale ÜF sınırlarını "
         "vermediğinden, sınırlar iki adımda belirlenmiştir: önce makaledeki açık çevrim görev oranı taraması "
         "(0,1 → 0,9 → 0,1) kendi modelimizde tekrarlanarak SInC ve CSI'nın aralıkları ölçülmüş, ardından pozitif SInC "
         "kümeleri, CSI ve ΔD ölçekleri üzerinde 12 noktalı bir ızgara taraması yapılmıştır "
         "(`experiments/baseline/tune_membership.py`). İlk tahminde \"SInC PS ve CSI ZE ise NM\" kuralı MPP'ye çok yakın "
         "devreye girip yüksek ışınımda görev oranında titreşime yol açmış; tarama bu kümeyi uzaklaştırarak sorunu "
         "gidermiştir. Nihai ÜF'ler ve kontrol yüzeyi Şekil 3 ve 4'te verilmiştir.", indent=True)
    figure("fis_membership.png", "Nihai üyelik fonksiyonları: SInC (7), CSI (5) ve ΔD (7 küme).", 15.5)
    figure("fis_surface.png", "SInC+CSI denetleyicisinin kontrol yüzeyi ΔD(SInC, CSI).", 8.5)
    h("5.4 Karşılaştırma yöntemleri ve makaleden sapmalar", 2)
    para("P&O, makaledeki ΔP/ΔV işaret kuralıyla, InC ise Denklem (4) ile gerçekleştirilmiştir. Makale bu yöntemlerde "
         "bir gerilim referansını PI döngüsüyle izler; burada [@elgendy12]'de de incelenen doğrudan görev oranı kontrolü "
         "seçilmiştir. Sabit adım ve periyot makalede verilmediğinden, adil karşılaştırma için 9 noktalı bir taramayla "
         "her aralıkta oturan ayarlar içinde en verimlisi (adım 0,005, periyot 1 ms) seçilmiştir. Bu bulgu, P&O "
         "parametrelerinin dönüştürücü dinamiğine göre seçilmesi gerektiğini gösteren [@femia] ile uyumludur. "
         "Tablo 3 makaleden bilinçli sapmaları özetler.", indent=True)
    table(["Konu", "Referans makale [@melhaoui]", "Bu çalışma", "Gerekçe"], [
        ["Ortam", "MATLAB/Simulink", "Python 3.14 (NumPy, SciPy, scikit-fuzzy)", "Açık, tekrar üretilebilir"],
        ["Dönüştürücü", "Anahtarlamalı model", "Ortalama durum-uzayı modeli", "Dinamik korunur, hız"],
        ["ÜF sınırları", "Verilmemiş", "Şekil 13 tekrarı + ızgara taraması", "Belgelenmiş tasarım"],
        ["MPPT periyodu", "Verilmemiş", "1 ms", "CSI ölçeği makaleyle uyumlu"],
        ["P&O / InC", "V_ref + PI", "Doğrudan ΔD, ayarlı adım", "Adil karşılaştırma"],
        ["Yakınsama süresi", "Tanımsız", "±%2 banda girip kalma süresi", "Ölçülebilir tanım"],
        ["RMS% (Denk. 14)", "√mean(P²)/P_opt", "√mean(P²)/√mean(P_opt²)", "P_opt zamanla değişiyor"],
    ], "Makaleden sapmalar ve gerekçeleri.", [2.8, 3.6, 5.0, 4.6], font_size=8.5)


def s6() -> None:
    h("6. Önerilen Geliştirme (Proposed Extension)")
    h("6.1 Gerekçe ve gürültü modeli", 2)
    para("MPP yakınında bir MPPT adımında panel gerilimindeki değişim yalnızca onlarca milivolttur. Denklem (5)'teki "
         "ikinci terim bu küçük farka böldüğü için ölçüm gürültüsünü büyütür; CSI, SInC'nin farkı olduğu için gürültüyü "
         "ikinci kez büyütür. Makale bu duyarlılığı yalnızca sözel olarak belirtmiştir. Etkiyi nicel olarak ölçmek için "
         "denetleyicinin gördüğü her örneğe sıfır ortalamalı Gauss gürültüsü eklenmiştir (tesis gürültüsüzdür):")
    eq("V_m = V + n_V,   n_V ~ N(0, (s · V_oc)²),     I_m = I + n_I,   n_I ~ N(0, (s · I_sc)²)")
    para("Burada s tam ölçeğe göre gürültü düzeyidir ve s ∈ {0; 0,1; 0,2; 0,5; 1} % değerleri incelenmiştir.")
    h("6.2 Sapmanın mekanizması", 2)
    para("ΔV gürültü düzeyine indiğinde artımsal terim sıfır ortalamalı ama ağır kuyruklu bir orana dönüşür ve "
         "SInC ≈ I/V + Δn_I/Δn_V olur. I/V her zaman pozitif olduğundan denetleyici sistematik olarak \"MPP'nin "
         "solundayım\" kararı verir ve D'yi alt sınıra doğru iter. P&O'da da dP/dV ≈ I + V·Δn_I/Δn_V olduğundan aynı "
         "yanlılık görülür. Bu nedenle sorun yalnızca filtreleme ile değil, paydanın gürültüden büyük tutulmasıyla "
         "çözülmelidir.", indent=True)
    h("6.3 Dayanıklı SInC kestiricisi", 2)
    para("Kestirici, ablasyon için ayrı ayrı kapatılabilen üç bileşenden oluşur ve kural tabanına dokunmaz:")
    bullets([
        "**F – ölçüm filtresi:** V ve I'ya birinci dereceden üstel hareketli ortalama uygulanır, "
        "x_f[k] = x_f[k−1] + α(x[k] − x_f[k−1]), α = 0,5.",
        "**D – birikimli fark ölü bölgesi:** dI/dV bir önceki örneğe göre değil, son güncellemenin referans örneğine "
        "göre ve yalnızca |V − V_ref| ≥ δ_V = 0,5 V olduğunda hesaplanır: dI/dV = (I − I_ref)/(V − V_ref); aksi halde "
        "önceki SInC korunur. Payda hiçbir zaman δ_V'den küçük olmadığı için gürültünün eğime etkisi yaklaşık "
        "√2·σ_I/δ_V ile sınırlanır.",
        "**C – kırpma:** SInC ±1,5 S ile sınırlanarak tek bir hatalı örneğin büyük bir CSI sıçraması üretmesi "
        "engellenir.",
    ])
    para("α ve δ_V, 12 noktalı bir ızgarada 100–102 tohumlarıyla seçilmiş; raporlanan sonuçlar ayrı 0–4 tohumlarıyla "
         "üretilmiştir (ayar ve test ayrımı). Adil karşılaştırma için aynı EMA filtresi P&O ve InC'ye, aynı kestirici "
         "tek girdili SInC denetleyicisine (Alg. 3) de uygulanmıştır.", indent=True)


def s7() -> None:
    h("7. Deney Düzeni (Experimental Setup)")
    table(["Öğe", "Değer"], [
        ["Donanım", "Intel Core i7-14650HX, 32 GB RAM, Windows 11 Pro"],
        ["Yazılım", "Python 3.14.6; NumPy 2.5.4 [@numpy], SciPy 1.18.1 [@scipy], scikit-fuzzy 0.5.0, pandas 3.1.1, matplotlib 3.11.2"],
        ["Tesis", "SPR-210 tek diyot modeli (n = 1), ortalama boost modeli, dt = 10 µs, ileri Euler"],
        ["Denetleyici", "T_s = 1 ms, D_0 = 0,1, 0,05 ≤ D ≤ 0,95"],
        ["Senaryolar", "Işınım basamakları (2 s, 25 °C); yük basamakları 50→20→35 Ω (0,6 s; 1000 ve 500 W/m²)"],
        ["Gürültü deneyi", "s = 0, 0,1, 0,2, 0,5, 1 % tam ölçek; 5 tohum (0–4); ayar tohumları 100–102"],
        ["Ölçütler", "η = ΣP_pv/ΣP_opt; RMSE; RMS%; yakınsama süresi (±%2 bant); görev oranı titreşimi"],
        ["Çalışma süresi", "2 s'lik bir benzetim ≈ 1–2 s; tüm gürültü deneyi ≈ 1 dk (paralel)"],
    ], "Deney ortamı ve parametreleri.", [3.2, 12.8], font_size=8.5)
    para("Tüm sonuçlar README'deki komutlarla yeniden üretilebilir; 22 birim testi model, kural tabanı, ölçütler ve "
         "kestirici için temel doğrulamaları yapar (pytest).", indent=True)


def s8() -> None:
    h("8. Sonuçlar (Results)")
    h("8.1 Tesis modelinin doğrulanması", 2)
    r1000 = f13[f13.G == 1000].iloc[0]
    para("Makaledeki açık çevrim taraması tekrarlandığında SInC ve CSI eğrileri makalenin Şekil 13'üyle aynı şekli "
         f"vermiştir (Şekil 5). 1000 W/m²'de SInC [{f(r1000.SInC_min)}; {f(r1000.SInC_max)}] aralığında "
         "(makale ≈ [−1,2; 1,25]), CSI'nın %5–95 aralığı "
         f"[{f(r1000.CSI_p05, 3)}; {f(r1000.CSI_p95, 3)}] (makale ≈ ±0,05) bulunmuştur.", indent=True)
    figure("fig13_duty_sweep_sinc_csi.png", "Açık çevrim görev oranı taraması: P_pv, SInC ve CSI ([@melhaoui] Şekil 13'ün "
           "yeniden üretimi).", 15.5)
    h("8.2 Işınım basamağı deneyi (makale Tablo 6)", 2)
    rows = []
    for _, r in t6.iterrows():
        rows.append([ALGO_TR[r.algorithm], f"{f(r.efficiency_pct)} ({f(r.paper_efficiency_pct)})",
                     f"{f(r.conv_avg_ms, 1)} ({f(r.paper_conv_avg_ms, 1)})", f"{f(r.rmse_w)} ({f(r.paper_rmse_w)})",
                     f"{f(r.rms_pct)} ({f(r.paper_rms_pct)})"])
    table(["Algoritma", "Verim %", "Ort. yakınsama (ms)", "RMSE (W)", "RMS %"], rows,
          "Işınım basamağı sonuçları; parantez içinde makalenin değeri [@melhaoui].", [4.4, 2.9, 3.3, 2.7, 2.7],
          bold_rows=(3,))
    para(f"Önerilen denetleyici %{N['eff_prop']} verim, {N['conv_prop']} ms ortalama yakınsama ve {N['rmse_prop']} W "
         "RMSE ile tüm ölçütlerde en iyi sonucu vermiş ve makaledeki sıralamayı doğrulamıştır (Tablo 5, Şekil 6). "
         "Mutlak değerler makaleden 0,5–1,5 puan farklıdır. t = 1,8 s'deki 600 → 200 W/m² geçişinde önerilen "
         "denetleyicinin tek girdili Alg. 3'ten çok daha hızlı toparlanması, CSI girdisinin düşük ışınımdaki "
         "yararını göstermektedir. 0,6 s ve 1,2 s'deki büyük düşüşlerden sonra tüm yöntemlerde görülen 30–50 ms'lik "
         "güç salınımı denetleyiciden değil, panel MPP'nin solunda akım kaynağı gibi çalıştığında zayıf sönümlenen "
         "L–C_e rezonansından kaynaklanır.", indent=True)
    figure("table6_power_duty.png", "Işınım basamağı deneyinde panel gücü ve görev oranı ([@melhaoui] Şekil 18–22 ile "
           "karşılaştırılabilir).", 15.5)
    h("8.3 Yük basamağı deneyi (makale Tablo 7)", 2)
    rows = [[str(int(r.G)), ALGO_TR[r.algorithm], f"{f(r.rmse_w)} ({f(r.paper_rmse_w)})", f"{f(r.rms_pct)} ({f(r.paper_rms_pct)})"]
            for _, r in t7.iterrows()]
    table(["G (W/m²)", "Algoritma", "RMSE (W)", "RMS %"], rows,
          "Yük basamağı sonuçları; parantez içinde makalenin değeri. Bu deney hiçbir ayarda kullanılmamıştır.",
          [2.4, 5.0, 3.2, 3.2])
    para(f"Önerilen denetleyicinin 1000 W/m²'deki RMSE değeri ({N['t7_1000']} W) makaledeki 25,15 W'a çok yakındır. ÜF'ler "
         "yalnızca ışınım senaryosunda ayarlandığı için bu deney bağımsız bir doğrulama niteliğindedir. InC'nin "
         "RMSE'si makaledekinden yüksektir; bunun nedeni InC'nin burada doğrudan görev oranı kontrolüyle ve sabit "
         "küçük adımla uygulanmasıdır.", indent=True)
    h("8.4 Ölçüm gürültüsü altında başarım (özgün katkı)", 2)
    variants = [("po", "P&O"), ("po+F", "P&O + filtre"), ("inc", "InC"), ("inc+F", "InC + filtre"),
                ("flc_sinc", "Alg. 3 (makale)"), ("alg3+FDC", "Alg. 3 + dayanıklı kestirici"),
                ("flc_sinc_csi", "Önerilen (makale)"), ("prop+FDC", "Önerilen + dayanıklı kestirici"),
                ("prop+FDC+gauss", "Dayanıklı + Gauss ÜF")]
    rows = []
    for v, name in variants:
        row = [name]
        for lv in (0.0, 0.2, 0.5, 1.0):
            m, s = eff(v, lv), effstd(v, lv)
            row.append(f(m) if lv == 0 else f"{f(m)} ± {f(s)}")
        rows.append(row)
    table(["Denetleyici", "s = 0", "s = 0,2 %", "s = 0,5 %", "s = 1 %"], rows,
          "Ölçüm gürültüsü altında ortalama MPPT verimi (%), 5 tohum ortalaması ± standart sapma.",
          [5.2, 2.0, 2.9, 2.9, 2.9], bold_rows=(7,))
    para(f"Gürültüsüz durumda en iyi olan önerilen denetleyici, s = %1'de %{N['n1']} ± {N['n1s']} verime düşmektedir; "
         f"bu düzeyde tek girdili Alg. 3'ün (%{N['a31']}) bile gerisindedir. P&O ve InC s = %0,5'te yaklaşık %40'a "
         f"çöker (P&O %{N['po05']}). Dayanıklı kestirici ile önerilen denetleyici s = %0,5'te %{N['r05']}, s = %1'de "
         f"%{N['r1']} ± {N['r1s']} verime ulaşır (Şekil 7, 9). Aynı kestiricinin verildiği Alg. 3, s = %1'de "
         f"%{N['a3r1']} ile en dayanıklı denetleyicidir; yalnızca filtre takılan P&O ve InC ise s = %0,5'in üzerinde "
         "toparlanamaz.", indent=True)
    figure("noise_efficiency_vs_level.png", "Gürültü düzeyine karşı ortalama verim (kesikli: makaledeki biçim, sürekli: "
           "dayanıklı/filtreli biçim).", 13.0)
    para("**Ablasyon.** s = %1'de yalnız F %" + N["F1"] + ", yalnız D %" + N["D1"] + " verim verirken ikisi birlikte %"
         + N["r1"] + " verir; bileşenler birbirini tamamlar (Şekil 8). C bileşeninin tek başına (%" + N["C1"] + ") ve "
         "F + D üzerine eklendiğinde ölçülebilir bir etkisi yoktur: ölü bölge paydayı sınırladığında SInC kırpma "
         "sınırına ulaşmaz. Gauss ÜF'ler s = %1'de verimi %" + N["g1"] + " ± " + N["g1s"] + " düzeyine taşıyarak "
         "değişkenliği azaltır, gürültüsüz durumda ise biraz geride kalır. Gürültüsüz durumda dayanıklı kestiricinin "
         f"bedeli %{N['n0']} → %{N['r0']} verim ve {N['conv_prop']} → {N['conv_r']} ms ortalama yakınsama süresidir.",
         indent=True)
    figure("noise_ablation.png", "Dayanıklı kestiricinin ablasyonu (F: EMA filtresi, D: ölü bölge, C: kırpma).", 14.5)
    figure("noise_timeseries_0p5pct.png", "s = %0,5 gürültüde makaledeki denetleyici (sol) ve dayanıklı kestiricili "
           "denetleyici (sağ).", 15.5)


def s9() -> None:
    h("9. Tartışma (Discussion)")
    para("Yeniden üretim, makalenin ana iddiasını nitel olarak doğrulamıştır: SInC+CSI denetleyicisi klasik yöntemlerden "
         "ve tek girdili SInC denetleyicisinden daha yüksek verim ve daha hızlı yakınsama sağlar. Mutlak sayılardaki "
         "farkların olası nedenleri (i) anahtarlama dalgalanmasının ortalama modelde bulunmaması, (ii) makalede "
         "verilmeyen ÜF sınırlarının yeniden tasarlanması, (iii) yakınsama süresinin farklı tanımlanması ve (iv) "
         "P&O/InC'nin doğrudan görev oranı kontrolüyle uygulanmasıdır. Bu nedenle sonuçlar mutlak değerler yerine "
         "sıralama ve göreli farklar üzerinden yorumlanmalıdır.", indent=True)
    para("CSI girdisinin etkisi koşula bağlıdır. Gürültüsüz durumda CSI, düşük ışınımda MPP'nin solunda kalan "
         "noktalar için adımı büyüterek belirgin bir hız kazandırır. Gürültü altında ise CSI, zaten gürültülü olan "
         "SInC'nin farkı olduğu için ek bir gürültü kaynağına dönüşür; dayanıklı kestirici kullanıldığında bile tek "
         "girdili Alg. 3'ün s = %1'de daha iyi olması bunu gösterir. Bu bulgu, girdi seçiminin yalnızca ideal ölçüm "
         "koşulunda değil, sensör kalitesiyle birlikte değerlendirilmesi gerektiğine işaret eder.", indent=True)
    para("Literatürde gürültüye karşı genellikle Type-2 bulanık mantık [@vidal,@boudia] veya sinir ağları "
         "[@intravaia] önerilmektedir. Bu çalışmadaki yaklaşım kural tabanını ve çıkarım tipini değiştirmeden, yalnızca "
         "girdi kestirimini düzelterek benzer bir dayanıklılık sağlar; ek hesaplama maliyeti bir filtre ve bir "
         "karşılaştırmadan ibarettir. Ayrıca sapmanın mekanizmasının (I/V teriminin pozitif yanlılığı) açıklanması, "
         "P&O ve InC'nin neden aynı şekilde başarısız olduğunu da açıklar ve yalnızca filtrelemenin neden yetmediğini "
         "gösterir. Son olarak SInC girdisinin [@shiau]'da daha önce önerilmiş olması, referans makalenin özgünlüğünün "
         "CSI ve genişletilmiş kural tabanıyla sınırlı olduğunu göstermektedir.", indent=True)


def s10() -> None:
    h("10. Sınırlılıklar (Limitations)")
    bullets([
        "Dönüştürücü ortalama modelle benzetilmiştir; anahtarlama dalgalanması, kayıplar ve ideal olmayan elemanlar "
        "yoktur. Donanım üzerinde doğrulama yapılmamıştır.",
        "ÜF sınırları ve P&O/InC parametreleri, Tablo 5'in raporlandığı ışınım senaryosunda ayarlanmıştır; yük "
        "deneyi ve gürültü deneyinin test tohumları bu ayardan bağımsızdır.",
        "Gürültü modeli örnek başına beyaz Gauss gürültüsüdür; ADC kuantalaması, sensör ofseti ve aşırı örnekleme "
        "modellenmemiştir. δ_V bir tasarım gürültü düzeyi için sabittir, çevrim içi kestirilmemektedir.",
        "Ağır gürültü altında ±%2 bandına dayalı yakınsama süresi anlamını yitirdiği için gürültü deneyi verim ve RMSE "
        "ile karşılaştırılmıştır.",
        "Kısmi gölgelenme ve çok tepeli P–V eğrileri incelenmemiştir; incelenen tüm denetleyiciler yerel tepeyi "
        "izleyen yöntemlerdir [@bollipo].",
        "Yalnızca Mamdani yapısı incelenmiştir; Sugeno ve Type-2 karşılaştırması yapılmamıştır.",
    ])


def s11() -> None:
    h("11. Sonuç (Conclusion)")
    para("Bu projede hibrit InC–bulanık MPPT denetleyicisi [@melhaoui] Python'da sıfırdan yeniden üretilmiş; PV "
         "modeli makaledeki tasarım noktasını birebir sağlamış, açık çevrim SInC/CSI davranışı makaleyle aynı şekli "
         f"vermiş ve önerilen denetleyici %{N['eff_prop']} verim ve {N['conv_prop']} ms yakınsama süresiyle makaledeki "
         "sıralamayı doğrulamıştır. Özgün katkı olarak, makalenin test etmediği ölçüm duyarlılığı nicelenmiş; tam "
         f"ölçeğin %1'i düzeyindeki gürültüde verimin %{N['n1']} düzeyine düştüğü ve bunun I/V teriminden kaynaklanan "
         "sistematik bir yanlılık olduğu gösterilmiştir. EMA filtresi ile birikimli fark ölü bölgesinden oluşan "
         f"dayanıklı SInC kestiricisi aynı koşulda verimi %{N['r1']} düzeyine çıkarmıştır. Gelecek çalışmalar olarak "
         "δ_V'nin gürültüden çevrim içi kestirilmesi, Type-2 bulanık kümelerle karşılaştırma, kısmi gölgelenme için "
         "global tarama ve anahtarlamalı model ya da donanım üzerinde doğrulama önerilmektedir.", indent=True)


def disclosure() -> None:
    h("Üretken Yapay Zekâ Kullanım Beyanı (Generative AI Usage Disclosure)")
    para("Bu projede Anthropic'in Claude Code aracı (Claude Opus 5.5 modeli) kapsamlı biçimde kullanılmıştır: "
         "makaleden parametre ve tabloların çıkarılması, PV/dönüştürücü modeli, bulanık çıkarım motoru, denetleyiciler "
         "ve deney betiklerinin yazılması, hata ayıklama, ızgara taramalarının tasarlanması, literatür taramasında "
         "aday kaynakların bulunması ve raporun ilk taslağının yazılması. Tüm kaynakların DOI, başlık, yazar ve "
         "yayın bilgileri Crossref üzerinden doğrulanmış; yalnızca okunan düzeyde (tam metin veya özet) iddialar "
         "kullanılmıştır (references/README.md). Raporlanan tüm sayılar depodaki betiklerin çıktılarından otomatik "
         "olarak alınmıştır. Proje kapsamı, katkı türü ve tasarım tercihleri öğrenci tarafından belirlenmiş; kod, "
         "sonuçlar ve bu rapor öğrenci tarafından incelenmiştir ve içerikten öğrenci sorumludur.", indent=True)


def references() -> None:
    h("Kaynakça (References)")
    for i, key in enumerate(_order, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(-0.8)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(f"[{i}]\t{REFS[key]}")
        r.font.size = Pt(9)
    unused = set(REFS) - set(_order)
    if unused:
        print("unused references:", sorted(unused))


def main() -> None:
    import sys
    sys.path.insert(0, str(ROOT))
    setup()
    title_block()
    for sec in (s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, disclosure, references):
        sec()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"saved {OUT}  figures={_fig[0]} tables={_tab[0]} equations={_eq[0]} refs={len(_order)}")


if __name__ == "__main__":
    main()
