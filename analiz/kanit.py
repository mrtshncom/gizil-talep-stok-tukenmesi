# -*- coding: utf-8 -*-
"""Kaynak-kanıt eşleşmesi: her atıflı cümlenin destekleyen pasajı, kaynağın kayıtlı özet veya açıklama metninde birebir aranır.
Pasajdaki '...' işareti, kaynağın aynı paragrafındaki iki ayrı birebir parçayı ayırır."""
import sys, os, re, csv, json, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kaynaklar as KY

def norm(s):
    s = unicodedata.normalize('NFKC', s)
    s = s.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"').replace('‐', '-').replace('–', '-').replace('—', '-').replace(' ', ' ')
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', s).strip().lower()

def ozet_metni(k):
    yol = os.path.join(KY.LIT, 'ozet', KY.DOI[k].replace('/', '_') + '.txt')
    if not os.path.exists(yol):
        yol = os.path.join(KY.LIT, 'ozet', KY.DOI[k].lower().replace('/', '_') + '.txt')
    return open(yol).read() if os.path.exists(yol) else ''

def ozet_kaynagi(k):
    yol = os.path.join(KY.LIT, 'ozet', KY.DOI[k].replace('/', '_') + '.kaynak')
    return open(yol).read().strip() if os.path.exists(yol) else 'Crossref veya DataCite kaydındaki özet'

def dogrula(k, pasaj):
    t = norm(ozet_metni(k) + ' ' + (KY.alanlar(k)[1] if k != 'veri' else ''))
    if not t: return False, 'özet metni yok'
    parca = [norm(p) for p in re.split(r'\s*\.\.\.\s*', pasaj) if p.strip()]
    eksik = [p for p in parca if p not in t]
    return (not eksik), ('' if not eksik else 'bulunamadı: ' + ' | '.join(x[:60] for x in eksik))

def tum_atiflar(bloklar):
    out = []
    for b in bloklar:
        if b[0] == 'p':
            for (m, k, pas, kon) in b[1]:
                if k: out.append((m, k, pas, kon))
    return out

if __name__ == '__main__':
    from icerik_giris import GIRIS
    from icerik_yontem import YONTEM
    from icerik_sonuc import SONUC
    from sayilar import CIKTI
    hata = 0; satir = []
    for m, k, pas, kon in tum_atiflar(GIRIS + YONTEM + SONUC):
        ok, neden = dogrula(k, pas)
        satir.append([k, KY.DOI[k], m, pas, ozet_kaynagi(k), 'eşleşti' if ok else neden])
        if not ok:
            hata += 1; print('HATA', k, neden, '|', m[:80])
    with open(os.path.join(CIKTI, 'kanit_raporu.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh); w.writerow(['kaynak', 'doi', 'cumle', 'destekleyen_pasaj', 'pasajin_arandigi_metin', 'sonuc']); w.writerows(satir)
    print('atıflı cümle', len(satir), 'toplam hata', hata)
