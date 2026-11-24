# -*- coding: utf-8 -*-
"""Kör hakem sürecinden ayrı yüklenen başlık sayfası. Yazar bilgileri yalnız bu dosyada yer alır.
Kullanım: python3 -I baslik_sayfasi.py <sablon.docx> <cikti.docx>"""
import sys, re, zipfile, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from icerik_oz_sabit import BASLIK_TR, BASLIK_EN, DEPO

SAB, OUT = sys.argv[1], sys.argv[2]
d = docx.Document(SAB)
body = d.element.body
for e in list(body):
    if e.tag != qn('w:sectPr'): body.remove(e)
for s in d.sections:
    for hf in [s.header, s.first_page_header, s.even_page_header, s.footer, s.first_page_footer, s.even_page_footer]:
        for t in hf._element.iter(qn('w:t')): t.text = ''
        for dr in list(hf._element.iter(qn('w:drawing'))): dr.getparent().remove(dr)

def par(metin='', b=False, sz=10, hiza=WD_ALIGN_PARAGRAPH.JUSTIFY, sonra=6, i=False):
    p = d.add_paragraph(); p.alignment = hiza
    p.paragraph_format.space_after = Pt(sonra); p.paragraph_format.space_before = Pt(0)
    if metin:
        for k, parca in enumerate(re.split(r'(\*\*[^*]+\*\*)', metin)):
            if not parca: continue
            kal = parca.startswith('**')
            r = p.add_run(parca.strip('*') if kal else parca); r.bold = b or kal; r.italic = i
            r.font.size = Pt(sz); r.font.name = 'Cambria'
            r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Cambria')
    return p

par('BAŞLIK SAYFASI', b=True, sz=12, hiza=WD_ALIGN_PARAGRAPH.CENTER, sonra=12)
par(BASLIK_TR, b=True, sz=12, hiza=WD_ALIGN_PARAGRAPH.CENTER)
par(BASLIK_EN, b=True, sz=12, hiza=WD_ALIGN_PARAGRAPH.CENTER, sonra=18)
par('Yazar Bilgileri', b=True, sz=10)
par('**Ad Soyad:** Murat ŞAHİN')
par('**Unvan:** Öğr. Gör. Dr.')
par('**Kurum:** Karadeniz Teknik Üniversitesi')
par('**İletişim adresi:** Karadeniz Teknik Üniversitesi, 61080 Trabzon, Türkiye')
par('**E-posta:** murat.sahinn@ktu.edu.tr')
par('**ORCID:** 0000-0001-8422-1350')
par('**Sorumlu yazar ve e-posta adresi:** Murat ŞAHİN, murat.sahinn@ktu.edu.tr', sonra=18)
par('Teşekkür', b=True)
par('Yazar, veri setini açık lisansla paylaşan veri sağlayıcısına teşekkür eder.', sonra=12)
par('Yazar Katkı Oranları', b=True)
par('Murat Şahin çalışmanın kavramsal ve tasarım süreçlerinin belirlenmesi, veri hazırlama, veri analizi, bulguların yorumlanması ve makalenin yazımı aşamalarının tamamını yürütmüştür (%100).', sonra=12)
par('Çıkar Çatışması', b=True)
par('Yazar, bilinen herhangi bir çıkar çatışması veya herhangi bir kurum, kuruluş ya da kişi ile ortak çıkar bulunmadığını onaylamaktadır.', sonra=12)
par('Etik Kurul Onayı', b=True)
par('Çalışmada insan ya da hayvan katılımcı bulunmamaktadır. Kullanılan veri seti CC BY 4.0 lisansıyla açık erişimde yayımlanmış, kimlik alanları kodlanmış ve kişisel veri içermeyen ikincil bir perakende işlem verisidir.', sonra=12)
par('Veri ve Kod Erişilebilirliği', b=True)
par(f'Veri seti: Smith (2026), Retail Transactions and Stocks Data, Mendeley Data, V1, doi:10.17632/27x8mjm8k4.1. Analiz kodu, veri kartı, ara çıktılar ve ek tablolar: {DEPO}')

cp = d.core_properties
cp.author = ''; cp.last_modified_by = ''; cp.title = ''; cp.subject = ''; cp.keywords = ''; cp.comments = ''; cp.category = ''
cp.revision = 1
d.save(OUT)

# paket temizliği: şablondan kalan özel XML, sözlük ve eklenti parçaları çıkarılır
zin = zipfile.ZipFile(OUT); tmp = OUT + '.tmp'; zout = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    v = zin.read(it.filename)
    if it.filename.startswith(('customXml/', 'word/webextensions/', 'word/glossary/')): continue
    if it.filename == '_rels/.rels': v = re.sub(rb'<Relationship [^>]*Target="word/webextensions/[^>]*/>', b'', v)
    if it.filename == '[Content_Types].xml': v = re.sub(rb'<Override PartName="/(customXml|word/webextensions|word/glossary)/[^>]*/>', b'', v)
    if it.filename == 'word/_rels/document.xml.rels':
        v = re.sub(rb'<Relationship [^>]*Target="\.\./customXml/[^>]*/>', b'', v); v = re.sub(rb'<Relationship [^>]*Target="glossary/[^>]*/>', b'', v)
    if it.filename == 'docProps/app.xml':
        s = v.decode(); s = re.sub(r'<Company>[^<]*</Company>', '<Company></Company>', s); s = re.sub(r'<Template>[^<]*</Template>', '<Template>Normal.dotm</Template>', s); v = s.encode()
    if it.filename == 'word/settings.xml': v = re.sub(rb'<w:attachedTemplate [^>]*/>', b'', v)
    if it.filename == 'docProps/core.xml':
        v = re.sub(rb'<dcterms:(created|modified) [^>]*>[^<]*</dcterms:(created|modified)>', b'', v)
    zout.writestr(it, v)
zout.close(); zin.close(); os.replace(tmp, OUT)
print(OUT)
