# -*- coding: utf-8 -*-
"""Ek tabloları ayrı bir Word dosyası ve her tablo için bir CSV dosyası olarak yazar.
Tablo, şekil ve kaynak numaraları makaledeki numaralarla aynıdır.
Kullanım: python3 -I ek_tablolar.py <cikis_klasoru>"""
import sys, os, re, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx.shared import Pt, Cm
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from icerik_giris import GIRIS
from icerik_yontem import YONTEM
from icerik_sonuc import SONUC
from icerik_ek import EK
from icerik_oz_sabit import BASLIK_TR
from tablolar import TUM
import kaynaklar as KY

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

# makaledeki numaralandırmanın aynısı (olustur.py ile aynı tarama sırası)
NUM, TNO, SNO, ENO = {}, {}, {}, {}
def numara(k):
    if k not in NUM: NUM[k] = len(NUM) + 1
    return NUM[k]
def hucre_ref(x):
    for k in re.findall(r'\{R:(\w+)\}', str(x)): numara(k)
for b in GIRIS + YONTEM + SONUC:
    if b[0] == 'p':
        for (m, k, _, _) in b[1]:
            if k: numara(k)
            hucre_ref(m)
    elif b[0] == 'table':
        TNO[b[1]] = len(TNO) + 1
        bas, sut, sat, notu = TUM[b[1]]()
        for h in [x for r in sat for x in r] + [notu, bas]: hucre_ref(h)
    elif b[0] == 'fig':
        SNO[b[1]] = len(SNO) + 1
for b in EK:
    ENO[b[1]] = len(ENO) + 1
    bas, sut, sat, notu = TUM[b[1]]()
    for h in [x for r in sat for x in r] + [notu, bas]: hucre_ref(h)

def coz(s):
    s = re.sub(r'\{R:(\w+)\}', lambda x: f'[{numara(x.group(1))}]', str(s))
    s = re.sub(r'\{T:(\w+)\}', lambda x: f'Tablo {TNO[x.group(1)]}', s)
    s = re.sub(r'\{EK:(\w+)\}', lambda x: f'Ek Tablo {ENO[x.group(1)]}', s)
    s = re.sub(r'\{S:(\w+)\}', lambda x: f'Şekil {SNO[x.group(1)]}', s)
    return s.replace('$', '')

d = docx.Document()
sec = d.sections[0]
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
for k in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'): setattr(sec, k, Cm(1.8))
st = d.styles['Normal']; st.font.name = 'Cambria'; st.font.size = Pt(9)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Cambria')

def par(t, b=False, sz=9, sonra=4):
    p = d.add_paragraph(); r = p.add_run(t); r.bold = b; r.font.size = Pt(sz)
    p.paragraph_format.space_after = Pt(sonra); return p

par('Ek Tablolar', b=True, sz=12)
par(BASLIK_TR, sz=10, sonra=10)
kullanilan = set()
for b in EK:
    bas, sut, sat, notu = TUM[b[1]]()
    no = ENO[b[1]]
    p = par(f'Ek Tablo {no}. ' + coz(bas), b=True, sz=9, sonra=2)
    t = d.add_table(rows=1 + len(sat), cols=len(sut)); t.style = 'Table Grid'
    for j, h in enumerate(sut):
        c = t.rows[0].cells[j]; c.text = ''; r = c.paragraphs[0].add_run(coz(h)); r.bold = True; r.font.size = Pt(8)
    for i, row in enumerate(sat):
        for j, h in enumerate(row):
            c = t.rows[i + 1].cells[j]; c.text = ''; r = c.paragraphs[0].add_run(coz(h)); r.font.size = Pt(8)
    if notu: par(coz(notu), sz=7.5, sonra=10)
    with open(os.path.join(OUT, f'ek_tablo_{no:02d}_{b[1]}.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh); cz = lambda x: coz(x).replace('\u2060', '')
        w.writerow([cz(x) for x in sut]); [w.writerow([cz(x) for x in r]) for r in sat]
    for r in sat:
        for h in r:
            for k in re.findall(r'\{R:(\w+)\}', str(h)): kullanilan.add(k)
    for k in re.findall(r'\{R:(\w+)\}', str(notu) + str(bas)): kullanilan.add(k)

if kullanilan:
    par('Ek tablolarda atıf yapılan kaynaklar', b=True, sz=9, sonra=2)
    for k in sorted(kullanilan, key=numara):
        parca, url = KY.apa(k)
        par(f'[{numara(k)}] ' + ''.join(m for m, _ in parca) + (url or ''), sz=8, sonra=2)

cp = d.core_properties
cp.author = ''; cp.last_modified_by = ''; cp.title = 'Ek Tablolar'; cp.comments = ''; cp.revision = 1
d.save(os.path.join(OUT, 'Ek_Tablolar.docx'))
print('ek tablo', len(EK))
