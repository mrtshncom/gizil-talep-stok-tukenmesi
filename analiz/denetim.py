# -*- coding: utf-8 -*-
"""Stok kaydı anlamının denetimi, örtük sıfır kuralı, etkin pencere ve sansür riski tanımları.
Kullanım: python3 -I denetim.py <cikti_klasor>"""
import sys, os, json
import numpy as np
out = sys.argv[1]
z = np.load(os.path.join(out, 'panel_ham.npz')); OH = z['OH'].astype(np.int32); G = z['G']; R = z['R']
P, T = OH.shape
has = OH != -999
res = {}
# 1) gün sonu / gün başı testi: ardışık iki günde kayıt varken stok düşüşü ile net satış eşleşmesi
both = has[:, 1:] & has[:, :-1]
dl = -(OH[:, 1:] - OH[:, :-1])
net = (G - R)
for ad, nt in (('ayni_gun', net[:, 1:]), ('onceki_gun', net[:, :-1])):
    x = dl[both]; y = nt[both]; m = y != 0
    res['anlam_' + ad] = dict(satis_gunu_n=int(m.sum()), tam_eslesme=float(np.mean(x[m] == y[m])),
                             satissiz_gun_n=int((~m).sum()), satissiz_degismez=float(np.mean(x[~m] == 0)))
# 2) kayıt bitişleri: son değer ve ertesi gün satış
anyrec = has.any(1)
first = np.where(anyrec, has.argmax(1), T)
last = np.where(anyrec, T - 1 - has[:, ::-1].argmax(1), -1)
ended = anyrec & (last < T - 1)
lq = OH[np.arange(P), np.clip(last, 0, T - 1)]
nx = G[np.arange(P), np.clip(last + 1, 0, T - 1)]
res['kayit_bitis'] = dict(biten=int(ended.sum()), acik=int((anyrec & (last == T - 1)).sum()),
    son1_n=int((ended & (lq == 1)).sum()), son1_ertesi_satis=float((nx[ended & (lq == 1)] > 0).mean()),
    son0_n=int((ended & (lq == 0)).sum()), son0_ertesi_satis=float((nx[ended & (lq == 0)] > 0).mean()))
idx = np.arange(T)[None, :]
before = idx < first[:, None]; after = idx > (last[:, None] + np.where(ended, 1, 0)[:, None])
inner = (~has) & ~before & (idx <= last[:, None])
res['kayitsiz_satis'] = dict(toplam_birim=float(G.sum()), kayit_hic_yok_seri=int((~anyrec).sum()),
    kayit_hic_yok_birim=float(G[~anyrec].sum()), ilk_oncesi_birim=float(G[before & anyrec[:, None]].sum()),
    ic_bosluk_gun=int(inner.sum()), ic_bosluk_birim=float(G[inner].sum()),
    bitis_ertesi_birim=float(G[np.arange(P)[ended], last[ended] + 1].sum()),
    etkin_sonrasi_birim=float(G[after & anyrec[:, None]].sum()))
# 3) örtük sıfır: ilk kayıttan son kayıt+1 güne kadar kayıtsız gün = 0
active = anyrec[:, None] & (idx >= first[:, None]) & (idx <= (last + np.where(ended, 1, 0))[:, None])
OHs = np.where(has, OH, 0); OHs = np.where(active, OHs, -999)
implicit = active & ~has
# örtük sıfır sonrası tutarlılık: tam eşleşme yeniden
b2 = active[:, 1:] & active[:, :-1]
x = -(OHs[:, 1:] - OHs[:, :-1])[b2]; y = net[:, 1:][b2]; m = y != 0
res['anlam_ortuk_sifir'] = dict(satis_gunu_n=int(m.sum()), tam_eslesme=float(np.mean(x[m] == y[m])))
# 4) stok akışı: giriş_t = OH_t - OH_{t-1} + satış_t - iade_t
inflow = np.zeros_like(OHs, dtype=np.float32)
inflow[:, 1:] = np.where(b2, OHs[:, 1:] - OHs[:, :-1] + net[:, 1:], np.nan)
opening = np.full_like(OHs, -999); opening[:, 1:] = np.where(b2, OHs[:, :-1], -999)
A = active
Y = np.where(A, G, 0)
neg = A & (OHs < 0)
sat_stoksuz = A & (G > 0) & (opening <= 0) & (opening != -999) & (inflow[:, :] <= 0)
kayip = A & (np.nan_to_num(inflow, nan=0) < 0)
res['kalite'] = dict(etkin_gun=int(A.sum()), etkin_seri=int(A.any(1).sum()), etkin_birim=float(Y.sum()),
    ortuk_sifir_gun=int(implicit.sum()), negatif_stok_gun=int(neg.sum()), negatif_stok_seri=int(neg.any(1).sum()),
    aciklanamayan_azalis_gun=int(kayip.sum()), satis_gunu=int((A & (G > 0)).sum()),
    pozitif_giris_gun=int((A & (np.nan_to_num(inflow) > 0)).sum()))
# 5) sansür riski tanımları
C1 = A & (OHs <= 0)                                   # geniş: gün sonu stok sıfır veya negatif
C2 = A & (OHs <= 1)                                   # ihtiyatlı: gün sonu stok bir veya daha az
A3 = A & ~implicit & ~neg                             # dar tanımın analiz kümesi: yalnız açık kayıtlı ve negatif olmayan günler
C3 = A3 & (OHs == 0)
satgun = A & (G > 0)
for ad, C, AA in (('CR1', C1, A), ('CR2', C2, A), ('CR3', C3, A3)):
    res[ad] = dict(gun=int(AA.sum()), sansurlu_gun=int(C.sum()), oran=float(C.sum() / AA.sum()),
                   satis_gunu_sansurlu=float((C & satgun & AA).sum() / (satgun & AA).sum()),
                   birim_sansurlu=float(Y[C & AA].sum() / Y[AA].sum()),
                   seri_sansur_orani_medyan=float(np.median((C.sum(1) / np.maximum(AA.sum(1), 1))[AA.any(1)])))
res['tukenme_gunu'] = dict(satisla_tukenen=int((C1 & satgun).sum()), tum_gun_stoksuz=int((C1 & ~satgun).sum()))
np.savez_compressed(os.path.join(out, 'panel.npz'), A=A, Y=Y.astype(np.float32), OH=OHs.astype(np.int16), C1=C1, C2=C2, C3=C3, A3=A3,
                    ST=z['ST'], PR=z['PR'], PROMO=z['PROMO'], NEG=neg, IMP=implicit)
json.dump(res, open(os.path.join(out, 'denetim.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
