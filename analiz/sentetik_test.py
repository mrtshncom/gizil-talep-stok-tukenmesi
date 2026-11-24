# -*- coding: utf-8 -*-
"""Veri setinin sentetik üretim izi taşıyıp taşımadığını sınayan bulgu tabanlı denetim.
Kullanım: python3 -I sentetik_test.py <ham_klasor> <cikti.json>
Sınamalar: (1) kimlik ve ad yapısı (anonimleştirme izi), (2) iade satırlarının aynı mağaza ve üründe önceki satışa
zamansal bağı ve rastgele tarih yer değiştirme ile karşılaştırma, (3) perakende takvim izleri, (4) fiyat sonları,
(5) iki bağımsız tablo arasındaki stok akışı tutarlılığı (denetim.json), (6) dağılım biçimi,
(7) operasyon izleri: stok girişlerinin haftanın gününe dağılımı ve maliyet üzerine fiyat oranı."""
import os
import sys, json, numpy as np, pandas as pd
ham, cik = sys.argv[1], sys.argv[2]
s = pd.read_csv(ham + '/retail_sales_ml_apl.csv'); inv = pd.read_csv(ham + '/retail_inventory_ml_apl.csv')
s['t'] = pd.to_datetime(s['Transaction Date'])
r = {}
# 1) kimlik ve ad yapısı
d = s['Product Description'].str.extract(r'^(PROD-\d+) (SEG-\d+) (.*)$')
ad = s['Product Segment'].str.split(' ', n=1).str[1]
r['kimlik'] = dict(aciklama_urun_no_eslesme=float((d[0] == s['Product No']).mean()),
                   aciklama_segment_eslesme=float((s['Product Segment'].str.split(' ').str[0] == d[1]).mean()),
                   ad_sozcuk_sayisi=int(len(set(' '.join(ad).split()))),
                   tedarikci=int(s['Supplier'].nunique()), kanal=s['Sales Channel'].unique().tolist(),
                   magaza_kod_ornek=sorted(s['Store'].unique())[:3])
# 2) iade-satış zamansal bağı
pos = s[s['Qty Sold'] > 0][['Store', 'Product No', 't']].sort_values('t')
ret = s[s['Qty Sold'] < 0][['Store', 'Product No', 't']].sort_values('t')
def bag(rr):
    m = pd.merge_asof(rr.sort_values('t'), pos.rename(columns={'t': 'ts'}), left_on='t', right_on='ts',
                      by=['Store', 'Product No'], direction='backward')
    lag = (m['t'] - m['ts']).dt.days
    return float(m['ts'].notna().mean()), float(lag.median()), float((lag <= 30).mean())
pay, med, p30 = bag(ret)
rng = np.random.default_rng(20260427); B = 200; pl = []
D0 = pd.Timestamp('2025-06-01')
for _ in range(B):
    rp = ret.copy(); rp['t'] = D0 + pd.to_timedelta(rng.integers(0, 328, len(rp)), 'D'); pl.append(bag(rp))
pl = np.array(pl)
r['iade_satis_bagi'] = dict(iade_satir=int(len(ret)), onceki_satis_payi=pay, gecikme_medyan_gun=med, gecikme_30_gun_payi=p30,
                            plasebo_onceki_satis_payi_ort=float(pl[:, 0].mean()), plasebo_onceki_satis_payi_max=float(pl[:, 0].max()),
                            plasebo_gecikme_medyan_ort=float(pl[:, 1].mean()), plasebo_gecikme30_ort=float(pl[:, 2].mean()),
                            plasebo_sayisi=B, p_degeri=float((1 + (pl[:, 0] >= pay).sum()) / (B + 1)))
# 3) takvim izleri
gun = s[s['Qty Sold'] > 0].groupby('t')['Qty Sold'].sum()
haf = gun.groupby(gun.index.dayofweek).mean()
def oran(tarih):
    t = pd.Timestamp(tarih); ayni = gun[(gun.index.dayofweek == t.dayofweek) & (abs((gun.index - t).days) <= 28) & (gun.index != t)]
    return float(gun.get(t, 0) / ayni.mean())
r['takvim'] = dict(en_yuksek_10_gun={str(k.date()): float(v) for k, v in gun.sort_values(ascending=False).head(10).items()},
                   haftanin_gunu_ort={int(k): float(v) for k, v in haf.items()},
                   cumartesi_pazartesi_orani=float(haf[5] / haf[0]),
                   bf_2025_11_28_ayni_gun_orani=oran('2025-11-28'), y_2025_12_24_ayni_gun_orani=oran('2025-12-24'),
                   sevgililer_2026_02_14_ayni_gun_orani=oran('2026-02-14'),
                   aylik={str(k): float(v) for k, v in gun.groupby(gun.index.to_period('M')).sum().items()})
# 4) fiyat sonları
up = (s.loc[s['Qty Sold'] > 0, 'Sales Amount'] / s.loc[s['Qty Sold'] > 0, 'Qty Sold']).round(2)
kurus = np.round((up % 1) * 100).astype(int)
r['fiyat'] = dict(sonu_99_payi=float((kurus == 99).mean()), sonu_00_payi=float((kurus == 0).mean()),
                  diger_payi=float(((kurus != 99) & (kurus != 0)).mean()))
# 5) dağılım biçimi
g = s[s['Qty Sold'] > 0].groupby(['Store', 'Product No', 't'])['Qty Sold'].sum()
sk = s[s['Qty Sold'] > 0].groupby('Product No')['Qty Sold'].sum().sort_values(ascending=False)
r['dagilim'] = dict(gunluk_birden_fazla_payi=float((g > 1).mean()),
                    ilk_yuzde10_sku_birim_payi=float(sk.head(int(len(sk) * 0.1)).sum() / sk.sum()),
                    stok_kaydi_1_birim_payi=float((inv['Qty on hand'] == 1).mean()),
                    stok_kaydi_negatif=int((inv['Qty on hand'] < 0).sum()))
# 7) operasyon izleri: stok girişleri (ardışık iki kayıtta stok artışı) ve fiyat/maliyet oranı
from scipy.stats import chisquare
inv['bas'] = pd.to_datetime(inv['Start Date'] if 'Start Date' in inv else inv.iloc[:, 0])
iv = inv.sort_values(['Store', 'Product No', 'bas'])
art = iv.groupby(['Store', 'Product No'])['Qty on hand'].diff() > 0
ev = iv.loc[art, ['Store', 'bas']]
wd = ev['bas'].dt.dayofweek.value_counts().sort_index()
chi = chisquare(wd.values)
def ust_pay(g_):
    c = np.bincount(g_, minlength=7); return c.max() / c.sum()
st_pay = ev.groupby('Store')['bas'].apply(lambda x: ust_pay(x.dt.dayofweek.values))
nst = ev.groupby('Store').size().values
rng2 = np.random.default_rng(20260427); sim = []
for _ in range(B):
    sim.append(np.median([np.bincount(rng2.integers(0, 7, k), minlength=7).max() / k for k in nst]))
sim = np.array(sim)
pp = s[(s['Qty Sold'] > 0) & (s['Cogs'] > 0)]
mk = pp['Sales Amount'] / pp['Cogs']; fp_ = pp[pp['Sales Type'] == 'Full Price']; mkf = fp_['Sales Amount'] / fp_['Cogs']
r['operasyon'] = dict(stok_girisi=int(len(ev)), gun_payi={int(k): float(v / wd.sum()) for k, v in wd.items()},
                      ki_kare=float(chi.statistic), ki_kare_p=float(chi.pvalue),
                      magaza_en_yogun_gun_payi_medyan=float(st_pay.median()), plasebo_medyan_ort=float(sim.mean()),
                      plasebo_medyan_max=float(sim.max()), plasebo_p=float((1 + (sim >= st_pay.median()).sum()) / (B + 1)),
                      fiyat_maliyet_medyan=float(mk.median()), fiyat_maliyet_ceyrek=[float(mk.quantile(.25)), float(mk.quantile(.75))],
                      tam_fiyat_maliyet_medyan=float(mkf.median()),
                      tam_fiyat_2_yakini=float(((mkf - 2).abs() <= 0.05).mean()))
json.dump(r, open(cik, 'w'), ensure_ascii=False, indent=1)
print(json.dumps(r, ensure_ascii=False, indent=1))
