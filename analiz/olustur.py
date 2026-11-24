# -*- coding: utf-8 -*-
"""Makaleyi JIET şablonuna dizer.
Kullanım: python3 -I olustur.py <sablon.docx> <cikti.docx> <sekil_klasoru>
Metin blokları icerik_*.py modüllerinden, sayılar analiz çıktılarından, kaynakça Crossref ve DataCite kayıtlarından gelir."""
import sys, os, re, copy, subprocess, tempfile, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx.shared import Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from lxml import etree
from icerik_giris import GIRIS
from icerik_yontem import YONTEM
from icerik_sonuc import SONUC
from icerik_oz import OZ_TR, OZ_EN, AK_TR, AK_EN, BEYAN, BASLIK_TR, BASLIK_EN, KISA_BASLIK
from icerik_ek import EK
from tablolar import TUM
import kaynaklar as KY

SABLON, CIKIS, SEKIL = sys.argv[1], sys.argv[2], sys.argv[3]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
XML = '{http://www.w3.org/XML/1998/namespace}space'

BLOKLAR = GIRIS + YONTEM + SONUC

# 1. Atıf, tablo ve şekil numaraları: belgedeki ilk geçiş sırasına göre (ek tablolar sona eklenir)
NUM = {}
def numara(k):
    if k not in KY.DOI: raise KeyError('DOI eşlemesi yok: ' + k)
    if k not in NUM: NUM[k] = len(NUM) + 1
    return NUM[k]
TABLO_NO = {}; SEKIL_NO = {}; EK_NO = {}
def tara_blok(b):
    if b[0] == 'p':
        for (m, k, _, _) in b[1]:
            if k: numara(k)
            for kk in re.findall(r'\{R:(\w+)\}', m): numara(kk)
    elif b[0] == 'table':
        TABLO_NO[b[1]] = len(TABLO_NO) + 1
        bas, sut, sat, notu = TUM[b[1]]()
        for hucre in [x for r in sat for x in r] + [notu, bas]:
            for k in re.findall(r'\{R:(\w+)\}', str(hucre)): numara(k)
    elif b[0] == 'fig':
        SEKIL_NO[b[1]] = len(SEKIL_NO) + 1
for b in BLOKLAR: tara_blok(b)
for b in EK:
    if b[0] == 'table':
        EK_NO[b[1]] = len(EK_NO) + 1
        bas, sut, sat, notu = TUM[b[1]]()
        for hucre in [x for r in sat for x in r] + [notu, bas]:
            for k in re.findall(r'\{R:(\w+)\}', str(hucre)): numara(k)
    elif b[0] == 'p':
        for (m, k, _, _) in b[1]:
            if k: numara(k)

def atifli(m, k):
    m = re.sub(r'\{R:(\w+)\}', lambda x: f'[{numara(x.group(1))}]', m)
    if not k: return m
    no = numara(k)
    if m.endswith('.'): return m[:-1] + f' [{no}].'
    return m + f' [{no}]'

def hucre_metni(s):
    s = re.sub(r'\{R:(\w+)\}', lambda x: f'[{numara(x.group(1))}]', str(s))
    s = re.sub(r'\{T:(\w+)\}', lambda x: f'Tablo {TABLO_NO[x.group(1)]}', s)
    s = re.sub(r'\{EK:(\w+)\}', lambda x: f'Ek Tablo {EK_NO[x.group(1)]}', s)
    s = re.sub(r'\{S:(\w+)\}', lambda x: f'Şekil {SEKIL_NO[x.group(1)]}', s)
    return s

def cozumle(m):
    return hucre_metni(m)

# 2. Matematik: pandoc ile LaTeX'ten OMML'e
MAT = {}
def mat_topla():
    satir = []; anahtar = []
    def ekle(lt, blok):
        if (lt, blok) in MAT or (lt, blok) in anahtar: return
        anahtar.append((lt, blok)); satir.append(('$$' + lt + '$$') if blok else ('$' + lt + '$'))
    def tara(s):
        for x in re.findall(r'\$([^$]+)\$', s): ekle(x, False)
    for b in BLOKLAR + EK:
        if b[0] == 'p':
            for (m, k, _, _) in b[1]: tara(m)
        elif b[0] in ('hip', 'madde'):
            for m in (b[1] if isinstance(b[1], list) else [b[1]]): tara(m)
        elif b[0] == 'eq': ekle(b[1], True)
        elif b[0] == 'table':
            bas, sut, sat, notu = TUM[b[1]]()
            for x in [bas, notu] + sut + [c for r in sat for c in r]: tara(str(x))
        elif b[0] == 'fig': tara(b[2])
    if not satir: return
    with tempfile.TemporaryDirectory() as td:
        md = os.path.join(td, 'm.md'); out = os.path.join(td, 'm.docx')
        open(md, 'w').write('\n\n'.join(satir) + '\n')
        subprocess.run(['pandoc', '-f', 'markdown', '-t', 'docx', md, '-o', out], check=True)
        x = etree.fromstring(zipfile.ZipFile(out).read('word/document.xml'))
    ps = x.findall('.//{%s}body/{%s}p' % (W, W))
    if len(ps) != len(anahtar): raise RuntimeError(f'pandoc paragraf sayısı {len(ps)} beklenen {len(anahtar)}')
    for (lt, blok), p in zip(anahtar, ps):
        el = p.find('.//{%s}oMath' % M)
        if el is None: raise RuntimeError('OMML üretilemedi: ' + lt)
        MAT[(lt, blok)] = el
mat_topla()

# 3. Şablon
d = docx.Document(SABLON)
body = d.element.body
els = list(body)
P_BASLIK = copy.deepcopy(els[7]); P_GOVDE = copy.deepcopy(els[8]); T_DENK = copy.deepcopy(els[18])
P_ALT = copy.deepcopy(els[29]); P_RESIM = copy.deepcopy(els[28]); P_KAY = copy.deepcopy(els[48])
P_SEC_TEK = copy.deepcopy(els[42])
SON = body.find(qn('w:sectPr'))
# örnek gövde içeriği (7-54) kaldırılır, başlık bölümü (0-6) korunur
for e in els[7:]:
    if e.tag != qn('w:sectPr'): body.remove(e)

def ekle(el): SON.addprevious(el); return el

def bos_p(proto=None):
    p = copy.deepcopy(proto if proto is not None else P_GOVDE)
    for c in list(p):
        if c.tag != qn('w:pPr'): p.remove(c)
    ppr = p.find(qn('w:pPr'))
    if ppr is not None:
        for c in list(ppr):
            if c.tag == qn('w:sectPr'): ppr.remove(c)
    return p

def _rpr(b=False, i=False, sz=20, sup=False, sub=False):
    rpr = OxmlElement('w:rPr')
    f = OxmlElement('w:rFonts'); f.set(qn('w:asciiTheme'), 'majorHAnsi'); f.set(qn('w:hAnsiTheme'), 'majorHAnsi'); f.set(qn('w:cs'), 'Times New Roman'); rpr.append(f)
    if b: rpr.append(OxmlElement('w:b')); rpr.append(OxmlElement('w:bCs'))
    if i: rpr.append(OxmlElement('w:i')); rpr.append(OxmlElement('w:iCs'))
    for t in ('w:sz', 'w:szCs'):
        s = OxmlElement(t); s.set(qn('w:val'), str(sz)); rpr.append(s)
    if sup or sub:
        v = OxmlElement('w:vertAlign'); v.set(qn('w:val'), 'superscript' if sup else 'subscript'); rpr.append(v)
    return rpr

def run(metin, b=False, i=False, sz=20, sup=False, sub=False):
    r = OxmlElement('w:r'); r.append(_rpr(b, i, sz, sup, sub))
    t = OxmlElement('w:t'); t.text = metin; t.set(XML, 'preserve'); r.append(t)
    return r

DESEN = re.compile(r'(\$[^$]+\$)|(\*\*[^*]+\*\*)|(\*[^*]+\*)')
def doldur(p, metin, sz=20, b=False, i=False):
    pos = 0
    for mt in DESEN.finditer(metin):
        if mt.start() > pos: p.append(run(metin[pos:mt.start()], b=b, i=i, sz=sz))
        s = mt.group(0)
        if mt.group(1):
            om = copy.deepcopy(MAT[(s[1:-1], False)])
            for rr in om.iter('{%s}r' % M):
                rpr = rr.find(qn('w:rPr'))
                if rpr is None:
                    rpr = OxmlElement('w:rPr'); rr.insert(0 if rr.find('{%s}rPr' % M) is None else 1, rpr)
                f = OxmlElement('w:rFonts'); f.set(qn('w:ascii'), 'Cambria Math'); f.set(qn('w:hAnsi'), 'Cambria Math'); rpr.insert(0, f)
                e = OxmlElement('w:sz'); e.set(qn('w:val'), str(sz)); rpr.append(e)
            p.append(om)
        elif mt.group(2):
            p.append(run(s[2:-2], b=True, i=i, sz=sz))
        else:
            p.append(run(s[1:-1], b=b, i=True, sz=sz))
        pos = mt.end()
    if pos < len(metin): p.append(run(metin[pos:], b=b, i=i, sz=sz))
    return p

def _jc(v):
    jc = OxmlElement('w:jc'); jc.set(qn('w:val'), v); return jc

def paragraf(metin, hiza='both', sz=20, b=False, i=False, sonra=0, sol=None, asili=None):
    p = bos_p(P_GOVDE); ppr = p.find(qn('w:pPr'))
    sp = ppr.find(qn('w:spacing')); sp.set(qn('w:after'), str(sonra))
    if sol is not None:
        ind = OxmlElement('w:ind'); ind.set(qn('w:left'), str(sol))
        if asili: ind.set(qn('w:hanging'), str(asili))
        ppr.insert(list(ppr).index(ppr.find(qn('w:jc'))), ind)
    ppr.find(qn('w:jc')).set(qn('w:val'), hiza)
    doldur(p, metin, sz=sz, b=b, i=i)
    return p

def bosluk(): ekle(bos_p(P_GOVDE))

def baslik(metin):
    p = bos_p(P_BASLIK); ppr = p.find(qn('w:pPr'))
    if ppr.find(qn('w:keepNext')) is None:
        kn = OxmlElement('w:keepNext'); ps_ = ppr.find(qn('w:pStyle')); (ps_.addnext(kn) if ps_ is not None else ppr.insert(0, kn))
    p.append(run(metin, b=True)); ekle(p)

def denklem(lt, no):
    t = copy.deepcopy(T_DENK)
    trs = t.findall(qn('w:tr'))
    for tr in trs[1:]: t.remove(tr)
    tcs = trs[0].findall(qn('w:tc'))
    p0 = tcs[0].find(qn('w:p')); p1 = tcs[1].find(qn('w:p'))
    for c in list(p0):
        if c.tag != qn('w:pPr'): p0.remove(c)
    para = etree.SubElement(p0, '{%s}oMathPara' % M)
    ppr = etree.SubElement(para, '{%s}oMathParaPr' % M); jc = etree.SubElement(ppr, '{%s}jc' % M); jc.set('{%s}val' % M, 'center')
    om = copy.deepcopy(MAT[(lt, True)])
    for rr in om.iter('{%s}r' % M):
        rpr = rr.find(qn('w:rPr'))
        if rpr is None:
            rpr = OxmlElement('w:rPr'); rr.insert(0 if rr.find('{%s}rPr' % M) is None else 1, rpr)
        f = OxmlElement('w:rFonts'); f.set(qn('w:ascii'), 'Cambria Math'); f.set(qn('w:hAnsi'), 'Cambria Math'); rpr.insert(0, f)
        e = OxmlElement('w:sz'); e.set(qn('w:val'), '20'); rpr.append(e)
    para.append(om)
    for c in list(p1):
        if c.tag != qn('w:pPr'): p1.remove(c)
    p1.append(run(f'({no})'))
    ekle(t)

def altyazi(tur, no, metin):
    p = bos_p(P_ALT)
    p.find(qn('w:pPr')).append(OxmlElement('w:keepNext')) if tur.endswith('Tablo') else None
    p.append(run(f'{tur} {no}.', b=True)); p.append(run(' '))
    doldur(p, metin)
    return p

def kenar(tcpr, ust=None, alt=None):
    b = OxmlElement('w:tcBorders')
    for ad, v in [('top', ust), ('left', None), ('bottom', alt), ('right', None)]:
        e = OxmlElement('w:' + ad)
        if v: e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), str(v)); e.set(qn('w:space'), '0'); e.set(qn('w:color'), '000000')
        else: e.set(qn('w:val'), 'nil')
        b.append(e)
    tcpr.append(b)

def tablo(anahtar, ek=False):
    bas, sut, sat, notu = TUM[anahtar]()
    if anahtar == 'literatur':
        # kaynak satırları kaynakçadaki numara sırasıyla verilir, çalışmanın kendi satırı en sonda kalır
        ks = [r for r in sat if re.match(r'\{R:\w+\}', str(r[0]))]; dg = [r for r in sat if r not in ks]
        sat = sorted(ks, key=lambda r: numara(re.match(r'\{R:(\w+)\}', r[0]).group(1))) + dg
    no = EK_NO[anahtar] if ek else TABLO_NO[anahtar]
    ekle(altyazi('Ek Tablo' if ek else 'Tablo', no, hucre_metni(bas)))
    nc = len(sut)
    tbl = OxmlElement('w:tbl'); tpr = OxmlElement('w:tblPr')
    tw = OxmlElement('w:tblW'); tw.set(qn('w:w'), '5000'); tw.set(qn('w:type'), 'pct'); tpr.append(tw)
    tpr.append(_jc('center'))
    lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'autofit'); tpr.append(lay)
    mar = OxmlElement('w:tblCellMar')
    for ad in ['left', 'right']:
        e = OxmlElement('w:' + ad); e.set(qn('w:w'), '57'); e.set(qn('w:type'), 'dxa'); mar.append(e)
    tpr.append(mar); tbl.append(tpr)
    grid = OxmlElement('w:tblGrid')
    for _ in range(nc): grid.append(OxmlElement('w:gridCol'))
    tbl.append(grid)
    tum = [sut] + sat
    for ri, r in enumerate(tum):
        tr = OxmlElement('w:tr')
        trpr = OxmlElement('w:trPr'); trpr.append(OxmlElement('w:cantSplit'))
        if ri == 0: trpr.append(OxmlElement('w:tblHeader'))
        tr.append(trpr)
        for ci, c in enumerate(r):
            tc = OxmlElement('w:tc'); tcpr = OxmlElement('w:tcPr')
            kenar(tcpr, ust=4 if ri == 0 else None, alt=(4 if ri == 0 else (4 if ri == len(tum) - 1 else None)))
            va = OxmlElement('w:vAlign'); va.set(qn('w:val'), 'center'); tcpr.append(va)
            tc.append(tcpr)
            p = OxmlElement('w:p'); ppr = OxmlElement('w:pPr')
            if ri < len(tum) - 1 and len(tum) < 25: ppr.append(OxmlElement('w:keepNext'))
            sp = OxmlElement('w:spacing'); sp.set(qn('w:before'), '10'); sp.set(qn('w:after'), '10'); sp.set(qn('w:line'), '240'); sp.set(qn('w:lineRule'), 'auto'); ppr.append(sp)
            ppr.append(_jc('left' if ci == 0 else 'center'))
            p.append(ppr)
            doldur(p, hucre_metni(c), sz=18, b=(ri == 0))
            tc.append(p); tr.append(tc)
        tbl.append(tr)
    ekle(tbl)
    if notu:
        ekle(paragraf(hucre_metni(notu), sz=18, hiza='both'))
    bosluk()

def sekil(anahtar, aciklama):
    no = SEKIL_NO[anahtar]
    yol = os.path.join(SEKIL, anahtar + '.png')
    tmp = d.add_paragraph()
    tmp.add_run().add_picture(yol, width=Cm(15.0) if anahtar.startswith('sekil1') or anahtar.endswith('_genis') else Cm(12.0))
    el = tmp._p; el.getparent().remove(el)
    pp = bos_p(P_GOVDE); ppr = pp.find(qn('w:pPr')); ppr.find(qn('w:jc')).set(qn('w:val'), 'center'); ppr.append(OxmlElement('w:keepNext'))
    for r in el.findall(qn('w:r')): pp.append(r)
    # görsel açıklama alanı: şekil başlığı
    for dp in pp.iter('{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr'):
        dp.set('name', f'Şekil {no}'); dp.set('descr', re.sub(r'\$[^$]*\$', '', hucre_metni(aciklama))[:200])
    for dp in pp.iter('{http://schemas.openxmlformats.org/drawingml/2006/picture}cNvPr'):
        dp.set('name', f'sekil{no}.png'); dp.attrib.pop('descr', None)
    ekle(pp)
    ekle(altyazi('Şekil', no, hucre_metni(aciklama)))
    bosluk()

def blok_yaz(b, onceki):
    if b[0] == 'h1':
        if onceki is not None: bosluk()
        baslik(b[1])
    elif b[0] == 'h2':
        if onceki not in ('h1', None): bosluk()
        baslik(b[1])
    elif b[0] == 'p':
        if onceki == 'p' or onceki == 'hip' or onceki == 'madde': bosluk()
        ekle(paragraf(cozumle(' '.join(atifli(m, k) for (m, k, _, _) in b[1] if m))))
    elif b[0] == 'hip':
        if onceki in ('p', 'madde'): bosluk()
        ekle(paragraf(cozumle(b[1]), i=True, sol=567))
    elif b[0] == 'madde':
        if onceki in ('p', 'hip'): bosluk()
        for k, m in enumerate(b[1]):
            ekle(paragraf(f'({k + 1}) ' + cozumle(m), sol=567, asili=340, sonra=60))
    elif b[0] == 'eq':
        denklem(b[1], b[2])
    elif b[0] == 'table':
        if onceki not in ('h1', 'h2'): bosluk()
        tablo(b[1])
    elif b[0] == 'fig':
        if onceki not in ('h1', 'h2', 'table', 'fig'): bosluk()
        sekil(b[1], b[2])

# 4. Başlık ve öz tablosu
t0 = d.tables[1]
def temizle_par(par):
    for r in list(par._p):
        if r.tag in (qn('w:r'), qn('w:hyperlink'), qn('w:bookmarkStart'), qn('w:bookmarkEnd')): par._p.remove(r)
def yaz_par(par, metin, b=False, sz=None, i=False):
    temizle_par(par)
    if metin:
        r = par.add_run(metin); r.bold = b; r.italic = i
        if sz: r.font.size = sz
c00 = t0.rows[0].cells[0]
ps = c00.paragraphs
from docx.shared import Pt
yaz_par(ps[0], BASLIK_TR, b=True, sz=Pt(12))
yaz_par(ps[2], ''); yaz_par(ps[3], '')
yaz_par(ps[5], '')   # kör hakem süreci: yazar adları ilk gönderimde boş bırakılır
c_ak = t0.rows[3].cells[0]; pk = c_ak.paragraphs
yaz_par(pk[0], 'Anahtar Kelimeler', b=True, sz=Pt(9))
akl = [x.strip() for x in AK_TR.split(',')]
for j, par in enumerate(pk[1:]):
    yaz_par(par, akl[j] if j < len(akl) else '', sz=Pt(9))
for kw in akl[len(pk) - 1:]:
    np_ = copy.deepcopy(pk[-1]._p); pk[-1]._p.addnext(np_)
    from docx.text.paragraph import Paragraph
    par = Paragraph(np_, pk[-1]._parent); yaz_par(par, kw, sz=Pt(9)); pk = c_ak.paragraphs
c_oz = t0.rows[3].cells[1]; po = c_oz.paragraphs[0]
temizle_par(po); r = po.add_run('Öz:'); r.bold = True; po.add_run(' ' + OZ_TR)
yaz_par(t0.rows[6].cells[0].paragraphs[0], BASLIK_EN, b=True, sz=Pt(12))
c_kw = t0.rows[9].cells[0]; pk = c_kw.paragraphs
yaz_par(pk[0], 'Keywords', b=True, sz=Pt(9))
akl = [x.strip() for x in AK_EN.split(',')]
for j, par in enumerate(pk[1:]):
    yaz_par(par, akl[j] if j < len(akl) else '', sz=Pt(9))
for kw in akl[len(pk) - 1:]:
    np_ = copy.deepcopy(pk[-1]._p); pk[-1]._p.addnext(np_)
    from docx.text.paragraph import Paragraph
    par = Paragraph(np_, pk[-1]._parent); yaz_par(par, kw, sz=Pt(9)); pk = c_kw.paragraphs
c_ab = t0.rows[9].cells[1]; pa = c_ab.paragraphs[0]
temizle_par(pa); r = pa.add_run('Abstract:'); r.bold = True; pa.add_run(' ' + OZ_EN)

# 5. Gövde
onceki = None
for b in BLOKLAR:
    blok_yaz(b, onceki); onceki = b[0]

# 6. Beyanlar (şablondaki sıra: Teşekkür, Yazar Katkı Oranları, Çıkar Çatışması)
for bas, metin in BEYAN:
    bosluk(); baslik(bas); ekle(paragraf(cozumle(metin)))

# 7. Kaynakça (APA, metindeki ilk geçiş sırasıyla numaralı)
bosluk(); baslik('Kaynakça')
sira = sorted(NUM, key=NUM.get)
rp0 = P_KAY.find(qn('w:r')).find(qn('w:rPr'))
for k in sira:
    parca, url = KY.apa(k)
    p = bos_p(P_KAY)
    ppr = p.find(qn('w:pPr')); r_ = ppr.find(qn('w:rPr'))
    if r_ is not None:
        for bb in r_.findall(qn('w:b')): r_.remove(bb)
    for metin, ital in parca:
        r = run(metin, i=ital); p.append(r)
    if url:
        rid = d.part.relate_to(url, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink', is_external=True)
        h = OxmlElement('w:hyperlink'); h.set(qn('r:id'), rid); h.set(qn('w:history'), '1')
        h.append(run(url)); p.append(h)
    ekle(p)

# 8. Ekler
if EK:
    bosluk(); baslik('Ekler')
    onceki = 'h1'
    for b in EK:
        if b[0] == 'table':
            if onceki not in ('h1', 'h2'): bosluk()
            tablo(b[1], ek=True)
        else:
            blok_yaz(b, onceki)
        onceki = b[0]

# 9. Üst bilgi ve dipnotlar: kör hakem süreci için yazar bilgisi boş bırakılır
for s in d.sections:
    for hf in [s.header, s.first_page_header, s.even_page_header, s.footer, s.first_page_footer, s.even_page_footer]:
        ts = list(hf._element.iter(qn('w:t')))
        metin = ''.join(t.text or '' for t in ts)
        if 'Çalışmanın' in metin or 'Soyad' in metin:
            for j, t in enumerate(ts): t.text = KISA_BASLIK if j == 0 else ''
        if 'Sorumlu yazar' in metin:
            for t in ts: t.text = ''
# sabit sayı olarak kalmış sayfa numaraları PAGE alanına çevrilir
def _fld(tur=None, instr=None):
    r = OxmlElement('w:r')
    if tur: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'), tur); r.append(e)
    if instr: e = OxmlElement('w:instrText'); e.set(XML, 'preserve'); e.text = instr; r.append(e)
    return r
for s_ in d.sections:
    for hf in [s_.footer, s_.first_page_footer, s_.even_page_footer]:
        el = hf._element
        if list(el.iter(qn('w:instrText'))): continue
        for t in list(el.iter(qn('w:t'))):
            if re.fullmatch(r'\d+', (t.text or '').strip()):
                r = t.getparent()
                r.addprevious(_fld('begin')); r.addprevious(_fld(instr=' PAGE ')); r.addprevious(_fld('separate'))
                r.addnext(_fld('end'))
for rel in d.part.rels.values():
    if rel.reltype.endswith('/footnotes'):
        fx = etree.fromstring(rel.target_part.blob)
        for f in fx.findall('{%s}footnote' % W):
            if f.get('{%s}type' % W) in ('separator', 'continuationSeparator'): continue
            for t in f.iter('{%s}t' % W): t.text = ''
        rel.target_part._blob = etree.tostring(fx, xml_declaration=True, encoding='UTF-8', standalone=True)
# başlık tablosundaki yazar satırının dipnot göstergeleri kaldırılır
for fr in list(t0._tbl.iter(qn('w:footnoteReference'))):
    r = fr.getparent(); r.getparent().remove(r)

# 10. Meta veri
cp = d.core_properties
cp.author = ''; cp.last_modified_by = ''; cp.title = ''; cp.subject = ''; cp.keywords = ''; cp.comments = ''; cp.category = ''
cp.revision = 1
st = d.settings.element
for dv in st.findall(qn('w:docVars')): st.remove(dv)
for rs in st.findall(qn('w:rsids')): st.remove(rs)
xml = etree.tostring(d.element).decode()
for rid, rel in list(d.part.rels.items()):
    if rel.reltype.split('/')[-1] in ('image', 'chart', 'hyperlink', 'oleObject', 'package') and f'"{rid}"' not in xml:
        del d.part.rels[rid]
for _t in d.element.body.iter(qn('w:t')):
    if _t.text and 'Araştırma /Derleme Makalesi' in _t.text: _t.text = _t.text.replace('Araştırma /Derleme Makalesi', 'Araştırma Makalesi')
d.save(CIKIS)

def paket_temizle(yol):
    zin = zipfile.ZipFile(yol); tmp = yol + '.tmp'
    zout = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED)
    for it in zin.infolist():
        veri = zin.read(it.filename)
        if it.filename.startswith('customXml/') or it.filename.startswith('word/webextensions/') or it.filename.startswith('word/glossary/'): continue
        if it.filename == '_rels/.rels':
            veri = re.sub(rb'<Relationship [^>]*Target="word/webextensions/[^>]*/>', b'', veri)
        if it.filename == 'docProps/app.xml':
            s = veri.decode()
            s = re.sub(r'<Company>[^<]*</Company>', '<Company></Company>', s)
            s = re.sub(r'<Template>[^<]*</Template>', '<Template>Normal.dotm</Template>', s)
            s = re.sub(r'<Manager>[^<]*</Manager>', '', s)
            veri = s.encode()
        if it.filename == '[Content_Types].xml':
            veri = re.sub(rb'<Override PartName="/(customXml|word/webextensions|word/glossary)/[^>]*/>', b'', veri)
        if it.filename == 'word/_rels/document.xml.rels':
            veri = re.sub(rb'<Relationship [^>]*Target="\.\./customXml/[^>]*/>', b'', veri)
            veri = re.sub(rb'<Relationship [^>]*Target="glossary/[^>]*/>', b'', veri)
        if it.filename == 'word/settings.xml':
            veri = re.sub(rb'<w:attachedTemplate [^>]*/>', b'', veri)
        if it.filename == 'docProps/core.xml':
            veri = re.sub(rb'<dcterms:created [^>]*>[^<]*</dcterms:created>', b'', veri)
            veri = re.sub(rb'<dcterms:modified [^>]*>[^<]*</dcterms:modified>', b'', veri)
            veri = re.sub(rb'<cp:lastPrinted>[^<]*</cp:lastPrinted>', b'', veri)
        zout.writestr(it, veri)
    zout.close(); zin.close(); os.replace(tmp, yol)
paket_temizle(CIKIS)
print('atif', len(NUM), 'tablo', len(TABLO_NO), 'ek', len(EK_NO), 'sekil', len(SEKIL_NO))
