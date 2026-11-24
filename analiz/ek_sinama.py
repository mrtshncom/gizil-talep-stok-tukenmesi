# -*- coding: utf-8 -*-
"""Ek sağlamlık sınamaları: seçim kaynaklı ortalamaya dönüş, havuzsuz tam bilgili kıyas, etiket hatasının
satış durumuna göre dağılımı, sıfır hedef stok payı, denetim paydası ve süre havuzu ayrıntıları.
Kullanım: python3 -I ek_sinama.py <cikti_klasor>"""
import sys, os, json
import numpy as np
out = sys.argv[1]
D = os.path.join(out, 'deney')
ORIG = [214, 242, 270, 298]; LTR = 112; H = 28; TOHUM = 20260427
res = {}

# 1) seçim kaynaklı ortalamaya dönüş: bilinen talep günlerinde test/eğitim günlük talep değişimi
z = np.load(os.path.join(out, 'panel.npz'))
A = z['A']; Yn = z['Y'].astype(float); OH = z['OH'].astype(np.int32); IMP = z['IMP']; NEG = z['NEG']
P, T = A.shape
KNOWN = A & ~IMP & ~NEG & (OH > 0)
YK = Yn * KNOWN
rtm = []
for k, t0 in enumerate(ORIG):
    tr = slice(t0 - LTR, t0); te = slice(t0, t0 + H)
    ntr = KNOWN[:, tr].sum(1); nte = KNOWN[:, te].sum(1); ytr = YK[:, tr].sum(1); yte = YK[:, te].sum(1)
    pop = (ntr >= 28) & (nte >= 1)
    d = np.load(os.path.join(D, f'S_orta_k{k}.npz'))
    sec = d['Dte'].sum() / d['nte'].sum() / (d['Dtr'].sum() / d['ntr'].sum()) - 1
    rtm.append(dict(baslangic=k, n_evren=int(pop.sum()),
                    evren_degisim=float(yte[pop].sum() / nte[pop].sum() / (ytr[pop].sum() / ntr[pop].sum()) - 1),
                    secilen_degisim=float(sec), tek_birim_payi=float((d['Ytr'] == 1).mean()),
                    secilen_n=int(len(d['Ytr']))))
res['ortalamaya_donus'] = rtm

# 2) havuzsuz tam bilgili kıyas: serinin gerçek eğitim talebi ortalaması × test penceresindeki bilinen gün
ps = [dict(np.load(os.path.join(D, f'S_orta_k{k}.npz'))) for k in range(4)]
c = lambda x: np.concatenate([q[x] for q in ps])
Dtr, ntr, nte, Dte = c('Dtr'), c('ntr'), c('nte'), c('Dte')
TB0 = Dtr / ntr * nte; TB = c('TB_te')
ks = {}
for m in ['M0', 'M1', 'M2', 'M3', 'M5', 'M6', 'M4', 'M4D', 'M4S', 'M4H', 'M4K', 'TB']:
    t = c(m + '_te')
    ks[m] = dict(ks_TB=float(np.abs(t - TB).sum() / TB.sum()), ks_TB0=float(np.abs(t - TB0).sum() / TB0.sum()),
                 test_wape=float(np.abs(t - Dte).sum() / Dte.sum()), test_yanlilik=float(t.sum() / Dte.sum() - 1))
res['kiyas_havuzsuz'] = ks
res['TB0_test_yanlilik'] = float(TB0.sum() / Dte.sum() - 1)

# 3) sıfır hedef stok payı ve karşılama oranı
sz = {}
for m in ['M0', 'M1', 'M2', 'M6', 'M4', 'M4S', 'TB', 'TK']:
    sz[m] = {str(cr): dict(sifir_stok=float((c(f'{m}_stok{cr}') == 0).mean()),
                           karsilama=float(c(f'{m}_sat{cr}').sum() / Dte.sum())) for cr in (50, 75, 90)}
res['sifir_stok'] = sz
res['test_talep_sifir'] = float((Dte == 0).mean())

# 4) yanlış pozitif hatada bayraklı günlerin satış durumuna göre gerçek sansürsüz payı
L = np.load(os.path.join(out, 'bosluk_sureleri.npy')); rng = np.random.default_rng(TOHUM)
pos = np.where(KNOWN[:, :ORIG[0]], OH[:, :ORIG[0]], 0).astype(float); pos[pos <= 0] = np.nan
with np.errstate(all='ignore'):
    S = np.nanmedian(pos, 1)
S = np.where(np.isnan(S), 1, np.maximum(1, np.round(S))).astype(np.int64)
Ys = np.zeros((P, T)); Cs = np.zeros((P, T), bool); stok = S.copy(); donus = np.full(P, -1)
for t in range(T):
    g = (donus >= 0) & (t >= donus); stok[g] = S[g]; donus[g] = -1
    k_ = KNOWN[:, t]; sat = np.where(k_, np.minimum(Yn[:, t], stok), 0); Ys[:, t] = sat; stok = stok - sat.astype(np.int64)
    y = k_ & (stok == 0) & (donus < 0)
    if y.any(): donus[y] = t + np.maximum(1, np.round(1.0 * rng.choice(L, y.sum()))).astype(np.int64)
    Cs[:, t] = k_ & (stok == 0)
# test penceresi koşulunun çıkardığı gözlem sayısı (orta şiddet)
dus = []
for k, t0 in enumerate(ORIG):
    tr = slice(t0 - LTR, t0); te = slice(t0, t0 + H)
    on = (KNOWN[:, tr].sum(1) >= 28) & ((Ys * KNOWN)[:, tr].sum(1) >= 1)
    dus.append(dict(on_kosul=int(on.sum()), test_kosulu_ile=int((on & (KNOWN[:, te].sum(1) >= 1)).sum())))
res['test_kosulu'] = dus
fp = {}
for eta in (5, 10, 20):
    sat0, sat1 = [], []
    for k, t0 in enumerate(ORIG):
        r = np.random.default_rng(TOHUM + k); Cn = Cs.copy(); m_ = ~Cn & KNOWN & (r.random(Cn.shape) < eta / 100); Cn[m_] = True
        tr = slice(t0 - LTR, t0); te = slice(t0, t0 + H)
        sel = (KNOWN[:, tr].sum(1) >= 28) & ((Ys * KNOWN)[:, tr].sum(1) >= 1) & (KNOWN[:, te].sum(1) >= 1)
        F = Cn[sel, tr] & KNOWN[sel, tr]; tru = Cs[sel, tr]; yy = Ys[sel, tr]
        sat0.append(float((~tru[F & (yy == 0)]).mean())); sat1.append(float((~tru[F & (yy >= 1)]).mean()))
    fp[f'FP{eta:02d}'] = dict(y0=float(np.mean(sat0)), y1=float(np.mean(sat1)))
res['fp_satis_durumu'] = fp

# 5) denetim paydası: pozitif satışlı günlerden ardışık kayıtlı ve net satışı sıfırdan farklı günlere
zh = np.load(os.path.join(out, 'panel_ham.npz')); OHh = zh['OH'].astype(np.int32); G = zh['G']; Rr = zh['R']
has = OHh != -999
anyrec = has.any(1); first = np.where(anyrec, has.argmax(1), T); last = np.where(anyrec, T - 1 - has[:, ::-1].argmax(1), -1)
ended = anyrec & (last < T - 1); idx = np.arange(T)[None, :]
active = anyrec[:, None] & (idx >= first[:, None]) & (idx <= (last + np.where(ended, 1, 0))[:, None])
both = np.zeros_like(has); both[:, 1:] = has[:, 1:] & has[:, :-1]
net = (G - Rr)
res['payda'] = dict(pozitif_satis_gun=int((G > 0).sum()), etkin_pozitif=int((active & (G > 0)).sum()),
                    etkin_disi_pozitif=int((~active & (G > 0)).sum()),
                    ardisik_kayitli_pozitif=int((both & (G > 0)).sum()),
                    ardisik_net_sifirdan_farkli=int((both & (net != 0)).sum()),
                    ardisik_pozitif_net_sifir_alti=int((both & (G > 0) & (net <= 0)).sum()),
                    ilk_kayit_gunu_pozitif=int((has & (G > 0) & (idx == first[:, None])).sum()),
                    ortuk_gun_pozitif=int((active & ~has & (G > 0)).sum()))

# 6) süre havuzu: son kayıt gününde süren stoksuz dönemler havuz dışında
z0 = A & (OH <= 0); ic, son = 0, 0
for p_ in range(P):
    a = z0[p_]
    if not a.any(): continue
    dd = np.diff(np.r_[0, a.astype(int), 0]); st = np.where(dd == 1)[0]; en = np.where(dd == -1)[0]
    la = np.where(A[p_])[0].max()
    for s_, e_ in zip(st, en):
        if e_ - 1 < la: ic += 1
        else: son += 1
res['sure_havuzu'] = dict(havuzda=ic, son_kayitta_suren=son, oran=son / max(ic + son, 1))

# 7) ayar ızgarası sınırları
res['izgara'] = dict(m6_alfa=[float(q['m6_alfa']) for q in ps], m2_w=[int(q['m2_w']) for q in ps],
                     m4h_phi=[float(q['M4H_phi']) for q in ps], em_tur={m: [int(q[m + '_em_tur']) for q in ps] for m in ('M4', 'M4S', 'TB', 'M4R')})
json.dump(res, open(os.path.join(out, 'ek_sinama.json'), 'w'), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
