# -*- coding: utf-8 -*-
"""Literatür taramasının yeniden üretilebilir kaydı.
Crossref arayüzünde önceden belirlenen sorgular çalıştırılır, her sorgu için toplam kayıt sayısı ve ilgi sırasına göre ilk
N kayıt saklanır. Çalışmada atıf yapılan kaynakların bu kayıtlarda bulunup bulunmadığı ayrıca işaretlenir.
Kullanım: python3 -I literatur_tarama.py <literatur_klasoru>"""
import sys, os, json, time, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kaynaklar as KY
LIT = sys.argv[1]
N = 50
SORGULAR = [
    'censored demand estimation lost sales retail',
    'stockout demand estimation sales data',
    'inventory record inaccuracy demand estimation',
    'newsvendor censored demand',
    'intermittent demand forecasting retail',
    'zero-inflated count demand',
    'empirical Bayes demand pooling retail',
    'forecast accuracy inventory performance',
    'probabilistic forecast evaluation count data',
    'data quality information systems',
]
FILTRE = 'until-pub-date:2026-10-31'
kayit = {'tarih': time.strftime('%Y-%m-%d'), 'arayuz': 'https://api.crossref.org/works', 'filtre': FILTRE, 'ilk_n': N, 'sorgular': []}
hedef = {v.lower(): k for k, v in KY.DOI.items()}
bulunan = set()
for q in SORGULAR:
    u = 'https://api.crossref.org/works?' + urllib.parse.urlencode({'query.bibliographic': q, 'rows': N, 'filter': FILTRE,
                                                                     'select': 'DOI,title,type,issued'})
    for deneme in range(4):
        try:
            m = json.load(urllib.request.urlopen(u, timeout=60))['message']; break
        except Exception as e:
            time.sleep(5 * (deneme + 1))
    else:
        raise RuntimeError('sorgu başarısız: ' + q)
    dois = [it['DOI'].lower() for it in m['items']]
    es = sorted(hedef[d] for d in dois if d in hedef); bulunan.update(es)
    kayit['sorgular'].append(dict(sorgu=q, toplam=m['total-results'], incelenen=len(dois),
                                  tur={t: sum(1 for it in m['items'] if it.get('type') == t) for t in {it.get('type') for it in m['items']}},
                                  atif_yapilan_eslesme=es, kayitlar=[dict(doi=it['DOI'], baslik=(it.get('title') or [''])[0]) for it in m['items']]))
    time.sleep(1)
kayit['sorgularda_bulunan_atif'] = sorted(bulunan)
kayit['sorgular_disi_atif'] = sorted(set(KY.DOI) - bulunan)
json.dump(kayit, open(os.path.join(LIT, 'tarama_kaydi.json'), 'w'), ensure_ascii=False, indent=1)
for s in kayit['sorgular']: print(s['sorgu'], s['toplam'], s['incelenen'], s['atif_yapilan_eslesme'])
print('sorgularda', len(bulunan), 'dışında', len(kayit['sorgular_disi_atif']))
