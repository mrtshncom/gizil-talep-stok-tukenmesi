# -*- coding: utf-8 -*-
"""Ham satış ve stok dosyalarından mağaza x SKU x gün paneli üretir.
Kullanım: python3 -I veri_hazirla.py <ham_klasor> <cikti_klasor>"""
import sys, json, hashlib, os
import numpy as np, pandas as pd
ham, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
fs = os.path.join(ham, 'retail_sales_ml_apl.csv'); fi = os.path.join(ham, 'retail_inventory_ml_apl.csv')
sha = {os.path.basename(f): hashlib.sha256(open(f, 'rb').read()).hexdigest() for f in (fs, fi)}
s = pd.read_csv(fs); i = pd.read_csv(fi)
D0 = pd.Timestamp('2025-06-01'); D1 = pd.Timestamp('2026-04-24'); T = (D1 - D0).days + 1
i['sd'] = (pd.to_datetime(i['Start Date']) - D0).dt.days
i['ed'] = (pd.to_datetime(i['End Date'].replace('9999-12-31', D1.strftime('%Y-%m-%d'))) - D0).dt.days
s['t'] = (pd.to_datetime(s['Transaction Date']) - D0).dt.days
k = ['Store', 'Product No']
pairs = pd.concat([i[k], s[k]]).drop_duplicates().sort_values(k).reset_index(drop=True)
pairs['pid'] = np.arange(len(pairs))
urun = pd.concat([i[['Product No', 'Product Division', 'Product Category', 'Product Subcategory', 'Product Segment']],
                  s[['Product No', 'Product Division', 'Product Category', 'Product Subcategory', 'Product Segment']]]).drop_duplicates('Product No')
pairs = pairs.merge(urun, on='Product No', how='left')
i = i.merge(pairs[k + ['pid']], on=k); s = s.merge(pairs[k + ['pid']], on=k)
P = len(pairs)
OH = np.full((P, T), -999, dtype=np.int16)          # gün sonu eldeki stok, -999 = kayıt yok
ST = np.full((P, T), -1, dtype=np.int8)             # stok fiyat durumu kodu
PR = np.full((P, T), np.nan, dtype=np.float32)      # birim satış fiyatı
durum = {'Full Price': 0, 'Promo': 1, 'Markdown Tier 1': 2, 'Markdown Tier 2': 3, 'Clearance': 4}
for pid, sd, ed, q, stt, pr in zip(i.pid.values, i.sd.values, i.ed.values, i['Qty on hand'].values,
                                   i['Stock Status'].map(durum).values, i['Stock Unit Selling Price'].values):
    OH[pid, sd:ed + 1] = q; ST[pid, sd:ed + 1] = stt; PR[pid, sd:ed + 1] = pr
G = np.zeros((P, T), dtype=np.float32); R = np.zeros((P, T), dtype=np.float32)
pos = s[s['Qty Sold'] > 0]; neg = s[s['Qty Sold'] < 0]
np.add.at(G, (pos.pid.values, pos.t.values), pos['Qty Sold'].values)
np.add.at(R, (neg.pid.values, neg.t.values), -neg['Qty Sold'].values)
PROMO = np.zeros((P, T), dtype=np.int8)   # satış günündeki satış türü promosyon veya indirim mi
pm = pos[pos['Sales Type'] != 'Full Price']
PROMO[pm.pid.values, pm.t.values] = 1
np.savez_compressed(os.path.join(out, 'panel_ham.npz'), OH=OH, G=G, R=R, ST=ST, PR=PR, PROMO=PROMO)
pairs.to_csv(os.path.join(out, 'seriler.csv'), index=False)
bilgi = dict(sha256=sha, satis_satir=int(len(s)), stok_satir=int(len(i)), T=int(T), P=int(P),
             tarih_bas=str(D0.date()), tarih_son=str(D1.date()),
             satis_tarih=[s['Transaction Date'].min(), s['Transaction Date'].max()],
             magaza=int(s.Store.nunique()), sku=int(pd.concat([s['Product No'], i['Product No']]).nunique()),
             bolum=int(pairs['Product Division'].nunique()), kategori=int(pairs['Product Category'].nunique()),
             altkategori=int(pairs['Product Subcategory'].nunique()), segment=int(pairs['Product Segment'].nunique()),
             iade_satir=int((s['Is Return'] == 1).sum()), sifir_adet_satir=int((s['Qty Sold'] == 0).sum()),
             iade_neden_bos=int(s['Reason of Return'].isna().sum()),
             satis_turu=s['Sales Type'].value_counts().to_dict(), stok_durumu=i['Stock Status'].value_counts().to_dict(),
             kanal=s['Sales Channel'].unique().tolist(), magaza_turu=i['Store Type'].unique().tolist(),
             stok_dup_baslangic=int(i.duplicated(k + ['Start Date']).sum()),
             stok_acik_uclu=int((i['End Date'] == '9999-12-31').sum()),
             stok_negatif_kayit=int((i['Qty on hand'] < 0).sum()), stok_sifir_kayit=int((i['Qty on hand'] == 0).sum()),
             eksik_hucre_satis=int(s.drop(columns=['Reason of Return']).isna().sum().sum()), eksik_hucre_stok=int(i.isna().sum().sum()),
             urun_tanim_tutarsiz=int((s.groupby('Product No')['Product Segment'].nunique() > 1).sum()))
json.dump(bilgi, open(os.path.join(out, 'veri_bilgi.json'), 'w'), ensure_ascii=False, indent=1, default=str)
print(json.dumps(bilgi, ensure_ascii=False, default=str)[:1500])
