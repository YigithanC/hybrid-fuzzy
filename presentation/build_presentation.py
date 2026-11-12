"""Build the Turkish presentation (presentation.pptx) with python-pptx.

    python presentation/build_presentation.py
    powershell -ExecutionPolicy Bypass -File presentation/export_pdf.ps1   # -> presentation.pdf

Every number on the slides comes from results/tables/*.csv (the same files the report uses).
Speaker notes (Turkish) are attached to each slide.
"""
import csv
import re
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.fuzzy_rules import CSI_LABELS, RULES_PROPOSED, SINC_LABELS  # noqa: E402

FIG = ROOT / "results" / "figures"
TAB = ROOT / "results" / "tables"
OUT = Path(__file__).resolve().parent / "presentation.pptx"

# ---- palette: night-sky ink with a sun-amber accent; teal marks our own contribution
INK = RGBColor(0x14, 0x21, 0x3D)
INK2 = RGBColor(0x2B, 0x3A, 0x55)
AMBER = RGBColor(0xF2, 0x9E, 0x1A)
TEAL = RGBColor(0x1F, 0x8A, 0x7D)
RED = RGBColor(0xC0, 0x39, 0x2B)
MUTED = RGBColor(0x5F, 0x6B, 0x7A)
CARD = RGBColor(0xEE, 0xF2, 0xF7)
CARD_T = RGBColor(0xE3, 0xF3, 0xF0)
CARD_A = RGBColor(0xFD, 0xF1, 0xDE)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LINE = RGBColor(0xC9, 0xD2, 0xDE)
HEAD, BODY = "Cambria", "Calibri"

W, H = 13.333, 7.5
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]
_count = [0]


# ------------------------------------------------------------------ numbers
def _csv(name):
    with open(TAB / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def tr(x, nd=2):
    """Turkish decimal comma."""
    return f"{float(x):.{nd}f}".replace(".", ",").replace("-", "−")


T6 = {r["algorithm"]: r for r in _csv("table6_reproduction.csv")}
T7 = _csv("table7_reproduction.csv")
NOISE = {}
with open(TAB / "noise_efficiency_table.csv", encoding="utf-8") as fh:
    rows = list(csv.reader(fh))
for r in rows[1:]:
    NOISE[r[0]] = [c.split(" ± ")[0] for c in r[1:]]   # 0, 0.1, 0.2, 0.5, 1 % FS


def nz(name, level):
    return float(NOISE[name][[0, 0.1, 0.2, 0.5, 1.0].index(level)])


# ------------------------------------------------------------------ helpers
TOKEN = re.compile(r"(\*\*.+?\*\*|_\{.+?\}|\^\{.+?\})")


def _runs(p, text, size, color, bold=False, font=BODY, italic=False):
    for part in TOKEN.split(text):
        if not part:
            continue
        r = p.add_run()
        b, base = bold, None
        if part.startswith("**"):
            part, b = part[2:-2], True
        elif part.startswith("_{"):
            part, base = part[2:-1], "-25000"
        elif part.startswith("^{"):
            part, base = part[2:-1], "30000"
        r.text = part
        f = r.font
        f.size, f.bold, f.italic, f.name = Pt(size), b, italic, font
        f.color.rgb = color
        if base:
            r._r.get_or_add_rPr().set("baseline", base)


def _bullet(p, level=0, color=AMBER):
    pPr = p._p.get_or_add_pPr()
    indent = Inches(0.28)
    pPr.set("marL", str(int(indent * (level + 1))))
    pPr.set("indent", str(-int(indent)))
    clr = etree.SubElement(pPr, qn("a:buClr"))
    etree.SubElement(clr, qn("a:srgbClr")).set("val", str(color))
    etree.SubElement(pPr, qn("a:buFont")).set("typeface", "Arial")
    etree.SubElement(pPr, qn("a:buChar")).set("char", "•" if level == 0 else "–")


def text(slide, x, y, w, h, lines, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT,
         font=BODY, anchor=MSO_ANCHOR.TOP, bullets=False, space=6, italic=False, name=None):
    """lines: str or list of str. A str starting with '- ' is a bullet, '-- ' a sub-bullet."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", 0)
    if isinstance(lines, str):
        lines = [lines]
    for k, line in enumerate(lines):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space)
        lvl = None
        if bullets or line.startswith("- ") or line.startswith("-- "):
            lvl = 1 if line.startswith("-- ") else 0
            line = line.lstrip("- ")
        _runs(p, line, size if lvl != 1 else size - 2, color, bold, font, italic)
        if lvl is not None:
            _bullet(p, lvl)
    return tb


def box(slide, x, y, w, h, fill=CARD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line=None, radius=0.06):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1)
    s.shadow.inherit = False
    s.text_frame.text = ""
    return s


def badge(slide, x, y, label, fill=AMBER, color=INK, d=0.5, size=16):
    s = box(slide, x, y, d, d, fill, MSO_SHAPE.OVAL)
    tf = s.text_frame
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", 0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _runs(p, label, size, color, True, HEAD)
    return s


def arrow(slide, x, y, w=0.4, h=0.32, fill=MUTED):
    return box(slide, x, y, w, h, fill, MSO_SHAPE.RIGHT_ARROW)


def image(slide, path, x, y, w=None, h=None):
    """Fit inside the w x h box, keep aspect, centre in the box."""
    from PIL import Image
    iw, ih = Image.open(path).size
    if w and h:
        scale = min(w / iw, h / ih)
        pw, ph = iw * scale, ih * scale
        x, y = x + (w - pw) / 2, y + (h - ph) / 2
    elif w:
        pw, ph = w, w * ih / iw
    else:
        pw, ph = h * iw / ih, h
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(pw), Inches(ph))


def table(slide, data, x, y, col_w, row_h=0.36, size=13, head_fill=INK, highlight=(),
          hl_fill=CARD_T, align_first=PP_ALIGN.LEFT, bold_rows=()):
    rows, cols = len(data), len(data[0])
    gf = slide.shapes.add_table(rows, cols, Inches(x), Inches(y), Inches(sum(col_w)),
                                Inches(row_h * rows))
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    tblPr.set("firstRow", "0")
    tblPr.set("bandRow", "0")
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Inches(cw)
    for i in range(rows):
        tbl.rows[i].height = Inches(row_h)
        for j in range(cols):
            c = tbl.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            if i == 0:
                c.fill.fore_color.rgb = head_fill
            elif i in highlight:
                c.fill.fore_color.rgb = hl_fill
            else:
                c.fill.fore_color.rgb = WHITE if i % 2 else CARD
            tf = c.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = align_first if j == 0 else PP_ALIGN.CENTER
            _runs(p, str(data[i][j]), size, WHITE if i == 0 else INK,
                  bold=(i == 0 or i in bold_rows))
    return tbl


def slide(title, dark=False, notes=""):
    s = prs.slides.add_slide(BLANK)
    _count[0] += 1
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = INK if dark else WHITE
    if title:
        text(s, 0.6, 0.38, W - 1.2, 0.8, title, 30, WHITE if dark else INK, True,
             font=HEAD, anchor=MSO_ANCHOR.MIDDLE, name="Title")
    if not dark:
        text(s, 0.6, H - 0.42, 8, 0.25,
             "Melhaoui vd. (2025) · Yeniden üretim ve gürültüye dayanıklı genişletme", 10, MUTED)
        text(s, W - 1.6, H - 0.42, 1.0, 0.25, str(_count[0]), 10, MUTED, align=PP_ALIGN.RIGHT)
    if notes:
        s.notes_slide.notes_text_frame.text = notes.strip()
    return s


# ================================================================== slides
# 1 — title
s = slide(None, dark=True, notes="""
(~30 sn) Merhaba. Projemde Scientific Reports'ta 2025'te yayımlanan, fotovoltaik sistemlerde
maksimum güç noktası takibi için hibrit bir bulanık mantık denetleyicisi öneren makaleyi inceledim.
Önce makalenin yöntemini sıfırdan Python'da yeniden ürettim, sonra makalenin test etmediği bir
zayıf noktayı, ölçüm gürültüsünü, inceleyip buna bir çözüm geliştirdim. Sonunda canlı demo yapacağım.
""")
box(s, 0.6, 0.9, 0.9, 0.9, AMBER, MSO_SHAPE.OVAL)
text(s, 0.6, 2.05, 11.5, 1.6, "Fotovoltaik Sistemlerde Hibrit Bulanık Mantık ile MPPT",
     40, WHITE, True, font=HEAD)
text(s, 0.6, 3.55, 11.5, 0.9,
     "Makalenin yeniden üretimi ve ölçüm gürültüsüne dayanıklı SInC kestiricisi", 22,
     RGBColor(0xC9, 0xD6, 0xEA))
text(s, 0.6, 4.75, 11.5, 1.2, [
    "Referans makale (No. 3): M. Melhaoui vd., “Hybrid fuzzy logic approach for enhanced MPPT "
    "control in PV systems,” Scientific Reports, 15:19235, 2025",
], 14, RGBColor(0xA9, 0xB8, 0xCE))
text(s, 0.6, 6.0, 11.5, 0.9, [
    "**Yiğithan Çalışkan** · 1306230049",
    "Bulanık Mantık · Dönem Projesi · 17 Kasım 2026",
], 16, WHITE, space=2)

# 2 — problem
s = slide("Problem: güneş paneli tek bir noktada en çok gücü verir", notes="""
(~1 dk) Bir PV panelin akım–gerilim eğrisi doğrusal değil; güç eğrisinin tek bir tepesi var,
buna maksimum güç noktası, MPP deniyor. Sorun şu: bu nokta ışınım ve sıcaklıkla yer değiştiriyor.
Grafikte görüldüğü gibi ışınım düşünce MPP gücü de, MPP gerilimi de değişiyor.
Panel ile yük arasına bir DC–DC yükseltici dönüştürücü koyuyoruz; anahtarlama oranı D'yi değiştirerek
panelin gördüğü direnci ayarlıyoruz. Bizim sistemde 1000 W/m²'de optimum D yaklaşık 0,61.
MPPT algoritmasının işi D'yi sürekli bu noktada tutmak. Uygulama alanı: çatı sistemleri, şebeke
bağlantılı inverterler, şarj denetleyicileri. Her yüzde birlik verim kaybı doğrudan enerji kaybı.
""")
image(s, FIG / "pv_curves.png", 0.6, 1.45, 7.6, 3.4)
text(s, 0.6, 4.95, 7.6, 0.4, "SunPower SPR-210 modeli: 1000 W/m²'de 210 W, R_{mpp} = 7,62 Ω",
     12, MUTED, italic=True)
for k, (big, small) in enumerate([("210 W", "1000 W/m²'de MPP gücü"),
                                  ("D = 0,61", "1000 W/m²'de optimum görev oranı"),
                                  ("1 ms", "MPPT karar periyodu")]):
    x = 0.6 + k * 4.1
    text(s, x, 5.55, 3.9, 0.75, big, 34, AMBER if k == 1 else INK, True, font=HEAD)
    text(s, x, 6.3, 3.9, 0.4, small, 14, INK2)
box(s, 8.6, 1.45, 4.15, 3.85, CARD)
text(s, 8.9, 1.65, 3.6, 3.6, [
    "**MPP sabit değil:** ışınım, sıcaklık ve yükle sürekli kayar",
    "**Çözüm:** yükseltici dönüştürücünün görev oranı D ayarlanır, R_{in} = R(1 − D)²",
    "**MPPT algoritması:** her 1 ms'de V, I ölçer ve ΔD kararı verir",
    "**Kullanım alanı:** çatı PV, şebeke inverterleri, batarya şarj denetleyicileri",
], 15, bullets=True, space=8)

# 3 — why fuzzy
s = slide("Klasik yöntemlerin sınırı ve bulanık mantığın gerekçesi", notes="""
(~1 dk) En yaygın iki yöntem P&O, yani değiştir ve gözle, ve artımsal iletkenlik InC.
İkisi de sabit adım kullanır. Büyük adım hızlı yakınsar ama MPP etrafında salınır; küçük adım az salınır
ama ışınım değişince yavaş kalır. Bu bir ödünleşim.
Bulanık mantık burada adımı uyarlamalı yapıyor: MPP'den uzaksan büyük, yakınsan küçük adım.
Bunu bir uzman gibi dilsel kurallarla ifade ediyoruz: "çok soldaysan D'yi çok azalt" gibi.
Ayrıca panelin tam matematiksel modeline ihtiyaç duymuyor; doğrusal olmayan sisteme uygun.
""")
for k, (head, col, fill, lines) in enumerate([
    ("Sabit adımlı P&O / InC", RED, CARD_A, [
        "Büyük adım → hızlı ama MPP etrafında **salınım**",
        "Küçük adım → az salınım ama **yavaş** takip",
        "Adım ve örnekleme periyodu dönüştürücüye göre elle ayarlanmalı",
    ]),
    ("Bulanık mantık denetleyici", TEAL, CARD_T, [
        "MPP'den uzaklığa göre **uyarlamalı adım** ΔD",
        "Uzman bilgisi dilsel kurallarla: “çok soldaysan D'yi çok azalt”",
        "Panelin kesin modeli gerekmez; doğrusal olmayan sisteme uygun",
    ]),
]):
    x = 0.6 + k * 6.2
    box(s, x, 1.5, 5.9, 3.5, fill)
    badge(s, x + 0.3, 1.75, "✕" if k == 0 else "✓", col, WHITE)
    text(s, x + 1.0, 1.75, 4.7, 0.5, head, 20, INK, True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.35, 2.55, 5.25, 2.4, lines, 17, bullets=True, space=12)
box(s, 0.6, 5.35, 12.1, 1.35, CARD)
text(s, 0.9, 5.35, 11.5, 1.35,
     "Makalenin sorusu: InC'nin bilgisini (SInC) bulanık denetleyiciye girdi yapıp, "
     "bir de değişim hızını (CSI) ekleyince takip ne kadar iyileşir?",
     17, INK2, italic=True, anchor=MSO_ANCHOR.MIDDLE)

# 4 — literature
s = slide("Literatür: benzer çalışmalar", notes="""
(~1,5 dk) Literatürü dört grupta taradım; tabloda en ilgili olanlar var.
Önemli bir bulgu: SInC girdisi yeni değil. Shiau ve arkadaşları 2015'te altı bulanık MPPT'yi
karşılaştırmış, bunlardan biri tam olarak SInC'yi tek girdi olarak kullanıyor. Yani referans makalenin
asıl katkısı CSI'yı ikinci girdi olarak eklemek.
Gürültü tarafında literatür genelde Type-2 bulanık mantık ya da sinir ağı öneriyor; Intravaia 2024
gürültü duyarlılığını P&O, InC ve sinir ağı için inceliyor ama bulanık InC için değil.
Bizim katkımız bu boşluğa denk geliyor: kurallara dokunmadan, sadece girdi kestirimini iyileştiriyoruz.
Toplam 23 kaynak var, hepsi raporda IEEE formatında.
""")
lit = [
    ["Çalışma", "Yöntem", "Ana fikir / girdiler", "Doğrulama", "Sonuç"],
    ["Shiau vd., 2015", "6 bulanık MPPT", "**SInC tek girdi** dahil", "Simülasyon",
     "Girdi seçiminin artı/eksileri"],
    ["Robles Algarín vd., 2017", "Mamdani FLC", "P&O ile kıyas", "Simulink, 65 W",
     "Daha az salınım ve kayıp"],
    ["Priyadarshi vd., 2020", "ANFIS + PSO", "Nöro-bulanık", "dSPACE deney",
     "P&O, PSO, ACO'dan iyi"],
    ["Boudia vd., 2025", "Type-2 FLC", "Belirsizlik ayak izi", "Simülasyon",
     "Type-1'den hızlı, az salınım"],
    ["Intravaia vd., 2024", "Gürültü analizi", "P&O, InC, YSA", "Simülasyon",
     "Belirsizlikte YSA en iyi"],
    ["**Melhaoui vd., 2025**", "InC + Mamdani", "**SInC + CSI**, 35 kural", "Simulink",
     "%97,7 verim, 53,5 ms"],
    ["**Bu çalışma**", "Yeniden üretim + kestirici", "SInC + CSI, filtre + ölü bölge",
     "Python", "%1 gürültüde %46 → %93"],
]
table(s, lit, 0.6, 1.45, [2.55, 2.2, 2.85, 1.9, 2.6], row_h=0.5, size=13,
      highlight=(6, 7), bold_rows=())
text(s, 0.6, 5.7, 12.1, 0.9, [
    "- SInC girdisi 2015'ten beri biliniyor → makalenin özgün kısmı **CSI** ve 5×7 kural tabanı",
    "- Gürültüye karşı literatür Type-2 veya YSA öneriyor; kural tabanına dokunmayan basit bir çözüm eksik",
], 14, space=4)

# 5 — theory 1
s = slide("Teori: bulanık küme ve dilsel değişken", notes="""
(~1,5 dk) Klasik kümede bir eleman ya içindedir ya değildir. Zadeh'in bulanık kümesinde
bir elemanın üyelik derecesi 0 ile 1 arasında bir sayıdır, μ_A(x).
Üyelik fonksiyonu bu dereceyi veren eğridir; biz üçgen kullanıyoruz, uçlarda omuz şeklinde.
Dilsel değişken, değerleri kelime olan değişkendir: SInC değişkeninin yedi terimi var: negatif büyük,
negatif orta, negatif küçük, sıfır, pozitif küçük, orta, büyük.
Bulanıklaştırma, ölçülen sayının her terime ne kadar ait olduğunu bulmaktır. Örneğin SInC = 0,05 için
"pozitif küçük" derecesi 0,56, "sıfır" derecesi 0,44. Komşu üçgenler toplamı 1 olacak şekilde
örtüşüyor; buna Ruspini bölüntüsü deniyor. Bu yüzden bir değer en fazla iki terimi ateşler.
""")
image(s, FIG / "fis_membership.png", 0.6, 1.4, 12.1, 3.2)
items = [
    ("μ", "Bulanık küme", "Üyelik derecesi μ_{A}(x) ∈ [0, 1]; keskin evet/hayır yerine derece"),
    ("△", "Üyelik fonksiyonu", "Üçgen + omuz; komşular toplamı 1 (Ruspini bölüntüsü)"),
    ("Aa", "Dilsel değişken", "SInC: NB … PB (7 terim), CSI: 5 terim, ΔD: 7 terim"),
    ("→", "Bulanıklaştırma", "SInC = 0,05 → PS: 0,56 ve ZE: 0,44"),
]
for k, (ic, head, body) in enumerate(items):
    x = 0.6 + k * 3.1
    box(s, x, 4.85, 2.9, 1.95, CARD)
    badge(s, x + 0.2, 5.05, ic, AMBER, INK, 0.5, 15)
    text(s, x + 0.85, 5.05, 1.95, 0.5, head, 15, INK, True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.2, 5.7, 2.55, 1.05, body, 13, INK2)

# 6 — theory 2
s = slide("Teori: Mamdani çıkarımı ve durulaştırma", notes="""
(~1,5 dk) Bulanık çıkarım dört adımdan oluşur. Bulanıklaştırmadan sonra kural tabanı gelir:
"EĞER SInC pozitif küçük VE CSI sıfır İSE ΔD negatif orta" gibi kurallar.
VE işlemi için minimum alınır; bu kuralın ateşlenme gücüdür. Mamdani yönteminde çıkış kümesi
bu güçte kırpılır, tüm kuralların çıkışları maksimum ile birleştirilir.
Durulaştırmada bu birleşik kümenin ağırlık merkezi alınır; sonuç tek bir sayı, ΔD.
Sugeno'da ise çıkış bir küme değil, sabit ya da doğrusal fonksiyondur; hesaplama daha ucuz ama
yorumlanabilirlik daha az. Makale Mamdani kullanıyor, ben de öyle uyguladım.
Type-2'de üyelik derecesinin kendisi de bulanık; gürültüye dayanıklılık için öneriliyor,
sonda bununla kıyaslayacağım.
""")
steps = [
    ("1", "Bulanıklaştırma", "SInC, CSI → üyelik dereceleri"),
    ("2", "Kural tabanı", "EĞER SInC = PS VE CSI = ZE\nİSE ΔD = NM"),
    ("3", "Mamdani çıkarımı", "VE = min, kırp,\nbirleştir = max"),
    ("4", "Durulaştırma", "Ağırlık merkezi\n→ tek sayı ΔD"),
]
for k, (n, head, body) in enumerate(steps):
    x = 0.6 + k * 3.15
    box(s, x, 1.5, 2.75, 2.2, CARD)
    badge(s, x + 0.2, 1.7, n)
    text(s, x + 0.85, 1.7, 1.8, 0.5, head, 15, INK, True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.2, 2.4, 2.4, 1.2, body.split("\n"), 14, INK2, space=2)
    if k < 3:
        arrow(s, x + 2.78, 2.45, 0.34, 0.3)
box(s, 0.6, 4.05, 5.9, 2.7, CARD_A)
text(s, 0.85, 4.25, 5.4, 2.4, [
    "**Ateşlenme gücü:** w = min(μ_{SInC}, μ_{CSI})",
    "**Birleştirme:** μ(u) = max_{k} min(w_{k}, μ_{k}(u))",
    "**Ağırlık merkezi:** ΔD = ∫ u·μ(u) du / ∫ μ(u) du",
], 17, space=14)
box(s, 6.8, 4.05, 5.9, 2.7, CARD)
text(s, 7.05, 4.25, 5.4, 2.4, [
    "- **Mamdani:** çıkış bulanık küme, yorumlanabilir → makalede ve bizde",
    "- **Sugeno:** çıkış sabit/doğrusal fonksiyon, ucuz hesap; ANFIS bunun öğrenen hâli",
    "- **Type-2:** üyelik derecesi de belirsiz (FOU); gürültüye karşı literatürde öneriliyor",
], 16, space=8)

# 7 — paper method: architecture
s = slide("Makalenin yöntemi: sistem mimarisi ve girdiler", notes="""
(~1,5 dk) Sistem: SPR-210 panel, yükseltici dönüştürücü ve 50 ohm yük. Denetleyici her 1 ms'de
panelin gerilim ve akımını örnekliyor.
Birinci girdi SInC: akım/gerilim artı akım değişimi/gerilim değişimi. Güç eğrisinin türevini sıfırlamak
bu toplamı sıfırlamakla aynı; yani MPP'de SInC sıfır. SInC pozitifse MPP'nin solundayız, D azaltılmalı;
negatifse sağındayız, D artırılmalı.
İkinci girdi CSI: SInC'nin bir önceki örneğe göre değişimi. Çalışma noktasının MPP'ye hangi hızla
yaklaştığını ya da uzaklaştığını söylüyor; aşmayı ve salınımı azaltmak için.
Çıkış ΔD; D'ye ekleniyor ve 0,05 ile 0,95 arasında sınırlanıyor.
""")
image(s, FIG / "system_diagram.png", 0.6, 1.35, 12.1, 3.0)
cards = [
    ("SInC", "SInC = I/V + ΔI/ΔV", "MPP'de 0 · > 0 ise solda → D↓ · < 0 ise sağda → D↑"),
    ("CSI", "CSI = SInC_{k} − SInC_{k−1}", "MPP'ye yaklaşma hızı; aşmayı ve salınımı azaltır"),
    ("ΔD", "D_{k} = D_{k−1} + ΔD", "Ağırlık merkeziyle bulunur, 0,05 ≤ D ≤ 0,95"),
]
for k, (b, eq, body) in enumerate(cards):
    x = 0.6 + k * 4.1
    box(s, x, 4.6, 3.85, 2.2, CARD)
    badge(s, x + 0.2, 4.8, b, INK, WHITE, 0.75, 13)
    text(s, x + 1.1, 4.8, 2.6, 0.75, eq, 16, INK, True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.25, 5.75, 3.4, 1.0, body, 14, INK2)

# 8 — MFs + rule base
s = slide("Kural tabanı: 5 × 7 = 35 Mamdani kuralı (makale Tablo 5)", notes="""
(~1,5 dk) Kural tabanı makaledeki Tablo 5. Satırlar CSI, sütunlar SInC.
Okuma örneği: SInC negatif büyükse, yani MPP'nin çok sağındaysak, CSI ne olursa olsun ΔD pozitif büyük:
D'yi hızla artır.
Ortadaki ilginç kısım: SInC küçükken CSI büyükse, yani nokta MPP'ye hızla yaklaşıyorsa,
çıkış sıfır: "zaten geliyorsun, dokunma". Bu aşmayı engelleyen kısım.
Makale üyelik fonksiyonlarının sayısal köşe noktalarını vermiyor. Ben D'yi 0,1'den 0,9'a tarayıp
SInC ve CSI'nın aldığı değer aralıklarını ölçtüm, köşe noktalarını buradan çıkardım, sonra
küçük bir ızgara aramasıyla ayarladım.
""")
grid = [["CSI \\ SInC"] + SINC_LABELS] + [[c] + [RULES_PROPOSED[c][si] for si in SINC_LABELS]
                                         for c in CSI_LABELS]
tbl = table(s, grid, 0.6, 1.5, [1.35] + [0.82] * 7, row_h=0.62, size=15,
            align_first=PP_ALIGN.CENTER, bold_rows=())
SHADE = {"PB": RGBColor(0xF6, 0xC1, 0x6B), "PM": RGBColor(0xFA, 0xDA, 0xA4),
         "PS": RGBColor(0xFD, 0xEE, 0xD3), "ZE": WHITE, "NS": RGBColor(0xD8, 0xEE, 0xEA),
         "NM": RGBColor(0xA9, 0xD9, 0xD1), "NB": RGBColor(0x6F, 0xBF, 0xB2)}
for i in range(1, 6):
    tbl.cell(i, 0).fill.fore_color.rgb = CARD
    for j in range(1, 8):
        tbl.cell(i, j).fill.fore_color.rgb = SHADE[grid[i][j]]
text(s, 0.6, 5.35, 7.1, 1.4, [
    "Turuncu: D artır (sağdayız) · Yeşil: D azalt (soldayız) · Beyaz: tut",
    "Hücre = ΔD terimi; satır CSI, sütun SInC",
], 13, MUTED, space=4)
box(s, 8.2, 1.5, 4.5, 5.25, CARD)
text(s, 8.45, 1.7, 4.05, 5.0, [
    "**Nasıl okunur?**",
    "- SInC = NB (çok sağda) → ΔD = **PB**, CSI ne olursa olsun",
    "- SInC küçük, CSI büyük (MPP'ye hızla geliyor) → **ZE**: “dokunma”, aşma önlenir",
    "- SInC = PS, CSI = ZE → **NM**: MPP'ye yakın ama solda",
    "**Üyelik fonksiyonları**",
    "- Makale köşe noktalarını vermiyor → D taraması ile aralık ölçüldü, ızgara aramasıyla ayarlandı",
], 14, space=7)

# 9 — control surface + worked example
s = slide("Kontrol yüzeyi ve bir çıkarım örneği", notes="""
(~1 dk) Kural tabanının bütün girdi uzayındaki karşılığı bu yüzey. SInC negatif tarafta yüzey
yukarıda, D artıyor; pozitif tarafta aşağıda. MPP civarında eğim yumuşak; bu küçük adımlar demek.
Sağda somut bir örnek: SInC 0,05, CSI 0. İki kural ateşleniyor: PS ve ZE için NM, gücü 0,56;
ZE ve ZE için ZE, gücü 0,44. Ağırlık merkezi ΔD = −0,0091 veriyor: D'yi biraz azalt.
Bu hesabı demoda kaydırıcılarla canlı göstereceğim.
""")
image(s, FIG / "fis_surface.png", 0.6, 1.35, 6.6, 5.5)
box(s, 7.5, 1.5, 5.2, 5.25, CARD_A)
text(s, 7.75, 1.7, 4.75, 0.5, "Örnek: SInC = 0,05, CSI = 0", 18, INK, True, font=HEAD)
text(s, 7.75, 2.4, 4.75, 4.3, [
    "**1. Bulanıklaştırma**",
    "SInC: PS = 0,56 · ZE = 0,44 · CSI: ZE = 1",
    "**2. Ateşlenen kurallar**",
    "PS ∧ ZE → NM, w = min(0,56; 1) = 0,56",
    "ZE ∧ ZE → ZE, w = 0,44",
    "**3. Kırp + birleştir (max)**",
    "**4. Ağırlık merkezi → ΔD = −0,0091**",
    "MPP'nin biraz solunda → D'yi küçük adımla azalt",
], 16, space=9)

# 10 — experimental setup
s = slide("Deneysel çalışma: ortam, parametreler, ölçütler", notes="""
(~1,5 dk) Makale MATLAB/Simulink kullanıyor ve kod paylaşmıyor; ben her şeyi Python'da sıfırdan yazdım.
Panel: tek diyot modeli; seri ve paralel direnci veri sayfasına tam oturacak şekilde fsolve ile buldum:
210 W ve 7,62 ohm, makaleyle aynı.
Dönüştürücü: ortalama durum uzayı modeli, 10 mikrosaniye adımla Euler.
Hazır veri seti yok: senaryolar sentetik. Makalenin Şekil 17 ışınım profili: her 0,2 saniyede
200 ile 1000 arasında basamak. Bir de yük basamağı testi: 50, 20, 35 ohm; bu test hiç ayar için
kullanılmadı.
Ölçütler: ortalama verim, RMSE, RMS yüzdesi ve ±%2 banda girip kalma süresi olarak yakınsama süresi.
""")
cards = [
    ("Ortam", ["Python 3.14, NumPy, SciPy, scikit-fuzzy", "Kod sıfırdan (makale kodu yok)",
               "23 birim testi"]),
    ("Model", ["SPR-210 tek diyot: 210 W, R_{mpp} = 7,62 Ω", "Boost: L = 12 mH, C_{e} = 150 µF, "
               "C_{o} = 250 µF, R = 50 Ω", "Euler 10 µs, MPPT periyodu 1 ms"]),
    ("Senaryolar", ["Şekil 17: 200–1000 W/m², 0,2 s basamak", "Yük basamağı 50 → 20 → 35 Ω "
                    "(ayar için **kullanılmadı**)", "25 °C"]),
    ("Ölçütler", ["Verim = ΣP_{pv} / ΣP_{opt}", "RMSE (W), RMS %", "Yakınsama: ±%2 banda girip kalma"]),
]
for k, (head, lines) in enumerate(cards):
    x = 0.6 + (k % 2) * 6.2
    y = 1.5 + (k // 2) * 2.7
    box(s, x, y, 5.9, 2.45, CARD)
    badge(s, x + 0.25, y + 0.22, str(k + 1))
    text(s, x + 0.95, y + 0.22, 4.7, 0.5, head, 18, INK, True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.3, y + 0.9, 5.4, 1.5, lines, 16, INK2, bullets=True, space=6)

# 11 — paper vs ours table
po, inc, a3, pr = (T6[k] for k in ("P&O", "InC", "Alg. 3 (SInC)", "Proposed (SInC+CSI)"))
s = slide("Makalenin sonuçları ve bizim yeniden üretimimiz", notes=f"""
(~1,5 dk) Bu tablo makalenin Tablo 6'sı; her hücrede önce bizim değer, parantezde makalenin değeri.
Makalenin ana iddiası: önerilen denetleyici en yüksek verim, en hızlı yakınsama ve en düşük hatayı
veriyor. Bu sıralama bizde de aynen çıktı: önerilen {tr(pr['efficiency_pct'])}, makalede 97,7.
Mutlak değerler yarım ile bir puan farklı. Nedenleri: ortalama dönüştürücü modeli, kendi
üyelik fonksiyonu köşe noktalarımız ve yakınsama süresinin tanımı; makale bunu tanımlamıyor.
Yakınsama sürelerimiz daha kısa çünkü biz ±%2 bandını kullandık.
""")
rows = [["Algoritma", "Verim %", "Yakınsama (ms)", "RMSE (W)", "RMS %"]]
paper = {"P&O": ("95,41", "65", "8,98", "96,34"), "InC": ("95,6", "60", "8,9", "96,4"),
         "Alg. 3 (SInC)": ("96,6", "76", "9,0", "96,89"),
         "Proposed (SInC+CSI)": ("97,7", "53,5", "8,6", "97,8")}
names = {"P&O": "P&O", "InC": "InC", "Alg. 3 (SInC)": "Alg. 3 (yalnız SInC)",
         "Proposed (SInC+CSI)": "**Önerilen (SInC + CSI)**"}
for key, r in [("P&O", po), ("InC", inc), ("Alg. 3 (SInC)", a3), ("Proposed (SInC+CSI)", pr)]:
    pp = paper[key]
    rows.append([names[key], f"{tr(r['efficiency_pct'])} ({pp[0]})",
                 f"{tr(r['conv_avg_ms'], 1)} ({pp[1]})", f"{tr(r['rmse_w'])} ({pp[2]})",
                 f"{tr(r['rms_pct'])} ({pp[3]})"])
table(s, rows, 0.6, 1.5, [3.4, 2.15, 2.25, 2.1, 2.2], row_h=0.6, size=16, highlight=(4,),
      bold_rows=(4,))
text(s, 0.6, 4.65, 12.1, 0.4, "Biçim: bizim değer (makalenin değeri) · Şekil 17 ışınım profili, 25 °C",
     12, MUTED, italic=True)
for k, (big, small, col) in enumerate([
    (f"%{tr(pr['efficiency_pct'])}", "önerilenin verimi (makale %97,7)", TEAL),
    ("4 / 4", "ölçütte sıralama makaleyle aynı", INK),
    ("±0,5–1", "puan mutlak fark: ortalama model, MF köşeleri", MUTED),
]):
    x = 0.6 + k * 4.1
    text(s, x, 5.15, 3.9, 0.85, big, 40, col, True, font=HEAD)
    text(s, x, 6.0, 3.9, 0.6, small, 14, INK2)

# 12 — time series + table 7
s = slide("Yeniden üretim: zaman yanıtı ve yük testi", notes="""
(~1 dk) Solda dört denetleyicinin güç ve D yanıtı; kırmızı noktalı çizgi ulaşılabilecek en yüksek güç.
P&O ve InC'de D'deki testere dişi salınım görülüyor; bulanık denetleyicilerde daha düzgün.
1,8 saniyedeki 600'den 200'e düşüşte Alg. 3 çok yavaş toparlanıyor; CSI eklenince hızlanıyor.
Bu makalenin iddiasıyla uyumlu.
Sağda yük basamağı testi: bu test hiç ayar için kullanılmadı, yani bağımsız bir doğrulama.
1000 W/m²'de önerilen RMSE 24,4; makalede 25,2. Çok yakın.
""")
image(s, FIG / "table6_power_duty.png", 0.6, 1.35, 7.4, 5.5)
rows = [["G", "Algoritma", "RMSE (W)", "RMS %"]]
for r in T7:
    lab = "InC" if r["algorithm"] == "InC" else "Önerilen"
    rows.append([r["G"], lab, f"{tr(r['rmse_w'])} ({tr(r['paper_rmse_w'])})", tr(r["rms_pct"])])
text(s, 8.3, 1.5, 4.4, 0.5, "Yük basamağı (50 → 20 → 35 Ω)", 16, INK, True, font=HEAD)
table(s, rows, 8.3, 2.05, [0.75, 1.25, 1.45, 0.95], row_h=0.46, size=13, highlight=(2, 4))
text(s, 8.3, 4.5, 4.4, 2.3, [
    "- Ayar için hiç kullanılmadı → **bağımsız test**",
    "- 1000 W/m²'de önerilen RMSE 24,4 (makale 25,2)",
    "- 1,8 s'deki düşüşte CSI, Alg. 3'e göre çok daha hızlı toparlıyor",
], 14, space=6)

# 13 — critique
s = slide("Eleştirel değerlendirme", notes="""
(~1,5 dk) Güçlü yönleri: rapor edilen iyileşme tutarlı ve biz de bağımsız olarak elde ettik;
kural tabanı yorumlanabilir; yöntem hesaplama olarak hafif.
Sınırlılıklar: üyelik fonksiyonlarının sayısal değerleri verilmemiş, bu yüzden tam aynısını
üretmek mümkün değil. Yakınsama süresi tanımlanmamış. Sadece simülasyon var, donanım yok.
Kısmi gölgelenmede güç eğrisi çok tepeli olur; SInC yerel tepede de sıfırdır, yani global MPP'yi
kaçırabilir. Bu test edilmemiş.
En önemlisi: makale kendi sonuç bölümünde ölçüm hassasiyetine ve bölmeye duyarlılığı bir sınırlılık
olarak yazıyor ama hiç test etmiyor. Benim katkım tam buradan çıkıyor.
""")
cols = [
    ("Güçlü yönler", TEAL, CARD_T, [
        "Tutarlı iyileşme: bağımsız yeniden üretimde de en iyi",
        "Yorumlanabilir 35 kural",
        "Hafif hesap, gömülü sisteme uygun",
    ]),
    ("Sınırlılıklar", AMBER, CARD_A, [
        "MF sayısal köşeleri ve yakınsama tanımı **verilmemiş**",
        "Yalnız simülasyon, donanım yok",
        "SInC'nin özgün olmadığı belirtilmemiş",
    ]),
    ("Olası başarısızlıklar", RED, RGBColor(0xF8, 0xE1, 0xDE), [
        "Kısmi gölgelenme: çok tepeli eğri, yerel tepede de SInC = 0",
        "**Ölçüm gürültüsü:** makale sınırlılık olarak yazıyor ama **test etmiyor**",
    ]),
]
for k, (head, col, fill, lines) in enumerate(cols):
    x = 0.6 + k * 4.1
    box(s, x, 1.5, 3.85, 3.75, fill)
    badge(s, x + 0.25, 1.72, "+" if k == 0 else ("!" if k == 1 else "✕"), col, WHITE)
    text(s, x + 0.95, 1.72, 2.8, 0.5, head, 18, INK, True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.3, 2.5, 3.3, 2.7, lines, 16, bullets=True, space=12)
box(s, 0.6, 5.55, 12.1, 1.15, INK)
text(s, 0.9, 5.55, 11.5, 1.15,
     "Katkının çıkış noktası: makale ölçüm hassasiyetine ve bölmeye duyarlılığı kendi sonuç "
     "bölümünde sınırlılık olarak yazıyor, ama bunu hiç ölçmüyor.",
     17, WHITE, anchor=MSO_ANCHOR.MIDDLE)

# 14 — contribution: the problem
s = slide("Özgün katkı: gürültüye çok duyarlı bir denetleyici", notes=f"""
(~1,5 dk) Neden gürültü? MPP civarında bir örnekten diğerine gerilim değişimi sadece onlarca milivolt.
Sensörde ±%0,5'lik gürültü 0,24 volt; yani ΔV neredeyse tamamen gürültü oluyor.
Bu durumda ΔI/ΔV sıfır ortalamalı rastgele bir oran olur ama I/V hep pozitif. SInC sistematik olarak
pozitife kayıyor; denetleyici sürekli "soldayım" sanıp D'yi alt sınıra itiyor. P&O'da da aynı mekanizma var.
CSI bir farkın farkı olduğu için gürültüyü bir kez daha büyütüyor.
Sonuç: %1 gürültüde önerilen denetleyicinin verimi yüzde {tr(nz('Proposed (paper)', 1.0), 1)},
P&O'nunki yüzde {tr(nz('P&O', 1.0), 1)} düzeyine düşüyor. Gürültüyü kontrolörün gördüğü her V ve I örneğine,
tam ölçeğin yüzdesi olarak ekledim, her seviye beş farklı tohumla.
""")
for k, (big, small, col) in enumerate([
    (f"%{tr(nz('Proposed (paper)', 0.0), 1)}", "gürültüsüz verim", TEAL),
    (f"%{tr(nz('Proposed (paper)', 0.5), 1)}", "σ = %0,5 tam ölçek", AMBER),
    (f"%{tr(nz('Proposed (paper)', 1.0), 1)}", "σ = %1 tam ölçek", RED),
]):
    x = 0.6 + k * 2.6
    text(s, x, 1.55, 2.5, 0.9, big, 40, col, True, font=HEAD)
    text(s, x, 2.45, 2.5, 0.5, small, 14, INK2)
text(s, 0.6, 3.0, 7.6, 0.4, "Önerilen denetleyici (makale), Şekil 17 profili, 5 tohum ortalaması",
     12, MUTED, italic=True)
box(s, 0.6, 3.5, 6.3, 2.7, CARD)
text(s, 0.85, 3.65, 5.85, 2.5, [
    "**Mekanizma: sistematik sapma**",
    "- MPP yakınında ΔV ≈ onlarca mV; %0,5 gürültü ≈ 0,24 V → ΔV çoğunlukla gürültü",
    "- SInC = I/V + (gürültü oranı) → I/V > 0 olduğu için **pozitife kayar**",
    "- Denetleyici sürekli “soldayım” der → D alt sınıra iner (P&O'da da aynı)",
    "- CSI = farkın farkı → gürültüyü bir kez daha büyütür",
], 14, space=4)
image(s, FIG / "noise_timeseries_0p5pct.png", 7.15, 3.5, 5.55, 2.65)
text(s, 7.15, 6.25, 5.55, 0.5, "σ = %0,5 · solda makalenin denetleyicisi, sağda dayanıklı sürüm "
     "(üstte güç, altta D)", 12, MUTED, italic=True)

# 15 — robust estimator
s = slide("Çözüm: gürültüye dayanıklı SInC kestiricisi", notes="""
(~1,5 dk) Çözümün ana fikri: bulanık kurallara ve üyelik fonksiyonlarına hiç dokunmamak;
sadece denetleyiciye giren SInC ve CSI'yı daha iyi kestirmek.
Üç parça var, her biri ayrı açılıp kapatılabiliyor, böylece ablasyon yapabildim.
F: gerilim ve akıma üstel hareketli ortalama filtresi, alfa 0,5.
D: biriktirilmiş fark ölü bölgesi. Türevi her örnekte değil, son referans örneğe göre hesaplıyorum ve
ancak gerilim farkı 0,5 voltu geçince güncelliyorum. Böylece paydadaki ΔV hiçbir zaman gürültü
seviyesine inmiyor. Bu, mekanizmadaki sapmanın kaynağını doğrudan kesiyor.
C: SInC'yi ±1,5'te kırpma.
Alfa ve delta değerlerini 100–102 tohumlarında seçtim; sonuçları farklı tohumlarda, 0–4'te raporluyorum.
Böylece ayar verisiyle test verisi ayrı.
""")
flow = [("V, I\n(gürültülü)", CARD), ("F: EMA filtre\nα = 0,5", CARD_T),
        ("D: ölü bölge\n|V − V_{ref}| ≥ 0,5 V", CARD_T), ("C: kırpma\n±1,5", CARD_T),
        ("SInC, CSI →\naynı 35 kural", CARD_A)]
for k, (lab, fill) in enumerate(flow):
    x = 0.6 + k * 2.5
    box(s, x, 1.55, 2.1, 1.25, fill)
    text(s, x + 0.1, 1.55, 1.9, 1.25, lab.split("\n"), 14, INK, True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, space=2)
    if k < 4:
        arrow(s, x + 2.13, 2.03, 0.34, 0.3)
box(s, 0.6, 3.2, 7.4, 3.0, CARD)
text(s, 0.85, 3.4, 6.9, 2.75, [
    "**Ölü bölge neden işe yarıyor?**",
    "- ΔI/ΔV, son referans örneğe göre ve yalnız |ΔV| ≥ δ_{V} olunca hesaplanır",
    "- Payda hiçbir zaman gürültü seviyesine inmez → **sapmanın kaynağı kesilir**",
    "- Arada SInC bir önceki değerini korur, CSI sıfıra yakın kalır",
    "**Kural tabanı ve MF'ler değişmez** → yorumlanabilirlik korunur",
], 16, space=7)
box(s, 8.3, 3.2, 4.4, 3.0, CARD_A)
text(s, 8.55, 3.4, 3.9, 2.75, [
    "**Adil deney tasarımı**",
    "- α, δ_{V}: ayar tohumları 100–102",
    "- Rapor: ayrı tohumlar 0–4",
    "- P&O ve InC'ye aynı filtre, Alg. 3'e aynı kestirici verildi",
    "- σ = 0 … %1 tam ölçek (V_{oc}, I_{sc})",
], 15, space=5)

# 16 — noise results
s = slide("Sonuç: %1 gürültüde verim %46'dan %93'e", notes=f"""
(~1,5 dk) Yatay eksende gürültü seviyesi, dikeyde ortalama verim, beş tohumun ortalaması ve
standart sapması. Kesikli çizgiler makaledeki denetleyiciler, düz çizgiler dayanıklı sürümler.
Önerilen denetleyicinin verimi %0,5 gürültüde yüzde {tr(nz('Proposed (paper)', 0.5), 1)} iken
kestiriciyle yüzde {tr(nz('Proposed + F + D + C (robust)', 0.5), 1)}; %1 gürültüde ise yüzde
{tr(nz('Proposed (paper)', 1.0), 1)} iken yüzde {tr(nz('Proposed + F + D + C (robust)', 1.0), 1)}.
Standart sapma da çok küçülüyor.
Sadece filtre eklemek P&O'yu kurtarmıyor: %1'de hâlâ %38. Yani sorun sadece gürültü genliği değil,
türevin kendisi; ölü bölge bu yüzden gerekli.
İlginç bir bulgu: gürültüde en dayanıklı olan, CSI'sız tek girdili Alg. 3'ün dayanıklı sürümü.
CSI temiz koşulda yardımcı ama gürültüde yüke dönüşüyor.
""")
image(s, FIG / "noise_efficiency_vs_level.png", 0.6, 1.35, 7.6, 5.4)
rows = [["Denetleyici", "%0,5", "%1"]]
for key, lab in [("P&O", "P&O"), ("P&O + filter", "P&O + filtre"),
                 ("Alg. 3 (paper)", "Alg. 3"), ("Alg. 3 + robust est.", "Alg. 3 + kestirici"),
                 ("Proposed (paper)", "Önerilen"),
                 ("Proposed + F + D + C (robust)", "**Önerilen + kestirici**")]:
    rows.append([lab, tr(nz(key, 0.5), 1), tr(nz(key, 1.0), 1)])
text(s, 8.5, 1.45, 4.2, 0.45, "Ortalama verim (%), 5 tohum", 15, INK, True, font=HEAD)
table(s, rows, 8.5, 1.95, [2.3, 0.95, 0.95], row_h=0.45, size=13, highlight=(4, 6), bold_rows=(6,))
text(s, 8.5, 5.25, 4.2, 1.5, [
    "- Yalnız filtre P&O'yu kurtarmıyor → sorun **türevde**",
    "- Gürültüde CSI yardımdan **yüke** dönüşüyor",
], 14, space=6)

# 17 — ablation + cost
s = slide("Ablasyon ve bedeli", notes=f"""
(~1,5 dk) Ablasyon: %1 gürültüde yalnız filtre {tr(nz('Proposed + F', 1.0), 1)}, yalnız ölü bölge
{tr(nz('Proposed + D', 1.0), 1)}, ikisi birlikte {tr(nz('Proposed + F + D', 1.0), 1)}. Yani iki parça birbirini
tamamlıyor: filtre genliği düşürüyor, ölü bölge paydayı koruyor.
Kırpmanın hiçbir etkisi yok; ölü bölge paydayı sınırlayınca SInC zaten kırpma sınırına ulaşmıyor.
Bunu dürüstçe raporluyorum: üç parçadan biri gereksiz çıktı.
Bedeli: gürültüsüz koşulda verim 98,2'den 97,0'a düşüyor, ortalama yakınsama 34'ten 95 ms'ye çıkıyor;
filtre gecikmesi ve ölü bölge yüzünden. Yani bu bir ödünleşim; gürültülü ortamda değerli.
Son olarak üçgen yerine Gauss üyelik fonksiyonu denedim: %1'de 93,3 ve sapma daha küçük.
""")
image(s, FIG / "noise_ablation.png", 0.6, 1.35, 7.6, 3.6)
text(s, 0.6, 5.05, 7.6, 0.4, "σ = %1 tam ölçek, önerilen denetleyici, 5 tohum", 12, MUTED, italic=True)
for k, (big, small, col) in enumerate([
    (f"%{tr(nz('Proposed + F', 1.0), 1)}", "yalnız F", INK),
    (f"%{tr(nz('Proposed + D', 1.0), 1)}", "yalnız D", INK),
    (f"%{tr(nz('Proposed + F + D', 1.0), 1)}", "F + D birlikte", TEAL),
]):
    x = 0.6 + k * 2.6
    text(s, x, 5.45, 2.5, 0.8, big, 32, col, True, font=HEAD)
    text(s, x, 6.25, 2.5, 0.4, small, 14, INK2)
box(s, 8.5, 1.45, 4.2, 2.45, CARD)
text(s, 8.75, 1.65, 3.75, 2.2, [
    "**Bulgular**",
    "- F ve D birbirini tamamlıyor",
    "- C'nin **etkisi yok** (D varken SInC sınıra ulaşmıyor)",
    f"- Gauss MF: %1'de %{tr(nz('Robust + Gaussian MF', 1.0), 1)}, daha küçük sapma",
], 14, space=5)
box(s, 8.5, 4.15, 4.2, 2.6, CARD_A)
text(s, 8.75, 4.35, 3.75, 2.3, [
    "**Bedeli (gürültüsüz)**",
    f"- Verim: %{tr(T6['Proposed (SInC+CSI)']['efficiency_pct'], 2)} → "
    f"%{tr(nz('Proposed + F + D + C (robust)', 0.0), 2)}",
    "- Ort. yakınsama: 34 → 95 ms",
    "- Neden: filtre gecikmesi ve ölü bölge",
], 14, space=5)

# 18 — live demo
s = slide("Canlı demo", notes="""
(~3 dk) Komut: python -m demo.
1) Deney sekmesi: senaryo "Özel basamaklar", 1000, 300, 700; gürültü önce 0. P&O, önerilen ve
   önerilen + dayanıklıyı seç, çalıştır. Üçü de iyi.
2) Gürültüyü %0,5'e çek, tekrar çalıştır: P&O yaklaşık %41'e, önerilen %87'ye düşer; dayanıklı %94 civarı kalır.
   D grafiğinde P&O'nun alt sınıra indiğini göster: anlattığım sapma bu.
3) Bulanık çıkarım sekmesi: SInC 0,05, CSI 0 → iki kural, ΔD = −0,0091. SInC'yi negatife çek:
   ΔD pozitif olur. CSI'yı büyüt: "dokunma" kuralı devreye girer.
Hoca bir koşul sorarsa (ör. 45 °C) sıcaklık kaydırıcısıyla anında dene.
""")
steps = [
    ("1", "Deney sekmesi", "1000 → 300 → 700 W/m², gürültü 0: P&O, Önerilen, Önerilen + kestirici"),
    ("2", "Gürültüyü %0,5 yap", "P&O ve önerilen çöker, dayanıklı sürüm ≈ %94'te kalır; D grafiğinde alt sınıra kayış"),
    ("3", "Bulanık çıkarım sekmesi", "SInC, CSI kaydırıcıları → ateşlenen kurallar, kırpılmış küme, ağırlık merkezi"),
    ("4", "Sizin koşulunuz", "Işınım, sıcaklık, yük, gürültü: istediğiniz değerle anında deney"),
]
for k, (n, head, body) in enumerate(steps):
    y = 1.5 + k * 1.3
    box(s, 0.6, y, 7.4, 1.1, CARD)
    badge(s, 0.85, y + 0.3, n)
    text(s, 1.55, y + 0.12, 6.2, 0.4, head, 16, INK, True)
    text(s, 1.55, y + 0.52, 6.3, 0.55, body, 13, INK2)
box(s, 8.3, 1.5, 4.4, 5.0, INK)
text(s, 8.6, 1.75, 3.8, 0.5, "Çalıştırma", 18, WHITE, True, font=HEAD)
text(s, 8.6, 2.35, 3.8, 1.0, ["cd fuzzy-mppt-project", "python -m demo"], 16, AMBER,
     font="Courier New", space=4)
text(s, 8.6, 3.5, 3.8, 3.0, [
    "- Tkinter arayüzü, 6 denetleyici",
    "- Bir deney 2–3 saniye",
    "- Kod ve sonuçlar GitHub'da: github.com/YigithanC/hybrid-fuzzy",
], 14, WHITE, space=8)

# 19 — conclusion
s = slide("Sonuç", dark=True, notes="""
(~1 dk) Özetle: makalenin yöntemini sıfırdan yeniden ürettim ve ana iddiasını doğruladım.
Makalenin test etmediği gürültü zayıflığını nicel olarak gösterdim ve mekanizmasını açıkladım.
Kural tabanına dokunmayan basit bir kestiriciyle %1 gürültüde verimi %46'dan %93'e çıkardım;
bedeli gürültüsüz koşulda biraz daha yavaş yakınsama.
Gelecek çalışma: gürültü seviyesini çevrim içi kestirip ölü bölgeyi uyarlamak, kısmi gölgelenme ve
Type-2 ile kıyas, donanımda doğrulama.
Yapay zekâ kullanımını raporda ayrı bir bölümde açıkladım. Teşekkürler, sorularınızı alabilirim.
""")
cols = [
    ("Yeniden üretim", [f"Önerilen: %{tr(pr['efficiency_pct'])} (makale %97,7)",
                        "Sıralama 4 ölçütte aynı", "Yük testi bağımsız doğrulandı"]),
    ("Özgün katkı", ["Gürültü zayıflığı ve sapma mekanizması gösterildi",
                     f"%1 gürültüde %{tr(nz('Proposed (paper)', 1.0), 1)} → "
                     f"%{tr(nz('Proposed + F + D + C (robust)', 1.0), 1)}",
                     "Kurallar değişmeden"]),
    ("Gelecek çalışma", ["Ölü bölgeyi gürültüye göre uyarlamak", "Kısmi gölgelenme, Type-2 kıyası",
                         "Donanımda doğrulama"]),
]
for k, (head, lines) in enumerate(cols):
    x = 0.6 + k * 4.1
    box(s, x, 1.55, 3.85, 3.3, INK2)
    badge(s, x + 0.25, 1.78, str(k + 1))
    text(s, x + 0.95, 1.78, 2.8, 0.5, head, 18, WHITE, True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.3, 2.55, 3.3, 2.2, lines, 16, WHITE, bullets=True, space=10)
text(s, 0.6, 5.3, 12.1, 0.8, "Teşekkürler · Sorular?", 36, AMBER, True, font=HEAD)
text(s, 0.6, 6.55, 12.1, 0.5,
     "Yapay zekâ kullanımı raporun “Üretken Yapay Zekâ Kullanım Beyanı” bölümünde açıklanmıştır. "
     "Kaynaklar: references/README.md (23 kaynak, IEEE)",
     12, RGBColor(0xA9, 0xB8, 0xCE))

prs.core_properties.title = "Fotovoltaik Sistemlerde Hibrit Bulanık Mantık ile MPPT"
prs.core_properties.author = "Yiğithan Çalışkan"
prs.save(OUT)
print(f"wrote {OUT} ({_count[0]} slides)")

# speaker notes as a separate file for rehearsal (the PDF does not carry notes)
md = ["# Konuşma notları", "",
      "`build_presentation.py` tarafından üretilir; slaytlardaki notlarla aynıdır.", ""]
for k, sl in enumerate(prs.slides, start=1):
    title = next((sh.text_frame.text for sh in sl.shapes if sh.name == "Title"), "Kapak")
    md += [f"## {k}. {title}", "", sl.notes_slide.notes_text_frame.text, ""]
(OUT.parent / "speaker_notes.md").write_text("\n".join(md), encoding="utf-8")
