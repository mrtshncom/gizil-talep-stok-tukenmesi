# -*- coding: utf-8 -*-
"""Kontrollü yeniden sansürleme, stok etiketi gürültüsü ve doğal veri deneyleri (ikinci sürüm).
Kullanım: python3 -I deney.py <cikti_klasor> <senaryo> <katman>
senaryo: S_dusuk | S_orta | S_yuksek | N_FN05 ... | N_FP20 | D_CR1 ... D_CR5
katman: 0-3 (dört yuvarlanan başlangıç noktası)"""
import sys, os, json, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modeller as Mo

out, sen, kat = sys.argv[1], sys.argv[2], int(sys.argv[3])
ORIG = [214, 242, 270, 298]; H = 28; LTR = int(os.environ.get('LTR', 112)); CRS = [0.5, 0.75, 0.9, 0.95]
KAPPA = {'S_dusuk': 0.25, 'S_orta': 1.0, 'S_yuksek': 2.0}
TOHUM = 20260427
z = np.load(os.path.join(out, 'panel.npz'))
A = z['A']; Yn = z['Y'].astype(np.float64); OH = z['OH'].astype(np.int32); IMP = z['IMP']; NEG = z['NEG']
ST = z['ST'].astype(np.int64); ST = np.where(ST < 0, 0, ST)
P, T = A.shape
ser = pd.read_csv(os.path.join(out, 'seriler.csv'))
SID_all = pd.factorize(ser['Store'])[0]; CID_all = pd.factorize(ser['Product Subcategory'])[0]
DIV_all = pd.factorize(ser['Product Division'])[0]
dow = (np.arange(T) + pd.Timestamp('2025-06-01').dayofweek) % 7
ilk = A.argmax(1); yas = np.arange(T)[None, :] - ilk[:, None]
YAS = np.digitize(yas, [14, 28, 56, 112]); YAS = np.where((ilk == 0)[:, None], 5, YAS)   # 5: veri başında zaten mevcut seri
def anahtar(t0):
    return (YAS * 35 + dow[None, :] * 5 + ST).astype(np.int64)
KNOWN = A & ~IMP & ~NEG & (OH > 0)       # gerçek talebin bilindiği günler (gün sonu stok pozitif)
BST = {}

def bosluk_dagilimi():
    z0 = A & (OH <= 0); L = []
    for p in range(P):
        a = z0[p]
        if not a.any(): continue
        d = np.diff(np.r_[0, a.astype(int), 0]); st = np.where(d == 1)[0]; en = np.where(d == -1)[0]
        la = np.where(A[p])[0].max()
        L += [e - s for s, e in zip(st, en) if e - 1 < la]
    return np.array(L)

def benzetim(kappa, rng):
    """Bilinen talep günleri üzerinde stok benzetimi. Kapasite S: serinin ilk başlangıç noktasından önceki
    pozitif stok değerlerinin medyanı. Tükenmeden sonra yenileme gecikmesi doğal tükenme sürelerinden çekilir."""
    Lf = os.path.join(out, 'bosluk_sureleri.npy')
    if not os.path.exists(Lf):
        gecici = f'{Lf}.{os.getpid()}.npy'; np.save(gecici, bosluk_dagilimi()); os.replace(gecici, Lf)
    L = np.load(Lf)
    pos = np.where(KNOWN[:, :ORIG[0]], OH[:, :ORIG[0]], 0).astype(float); pos[pos <= 0] = np.nan
    with np.errstate(all='ignore'):
        S = np.nanmedian(pos, axis=1)
    S = np.where(np.isnan(S), 1, np.maximum(1, np.round(S))).astype(np.int64)
    Ys = np.zeros((P, T)); Cs = np.zeros((P, T), bool)
    stok = S.copy(); donus = np.full(P, -1); BST['kap_var'] = ~(~np.isnan(pos)).any(1)
    tuk = []
    for t in range(T):
        geri = (donus >= 0) & (t >= donus)
        stok[geri] = S[geri]; donus[geri] = -1
        k = KNOWN[:, t]
        sat = np.where(k, np.minimum(Yn[:, t], stok), 0)
        Ys[:, t] = sat; stok = stok - sat.astype(np.int64)
        yeni = k & (stok == 0) & (donus < 0)
        if yeni.any():
            lag = np.maximum(1, np.round(kappa * rng.choice(L, yeni.sum()))).astype(np.int64)
            donus[yeni] = t + lag
            tuk += list(zip(np.where(yeni)[0], np.full(yeni.sum(), t), t + lag))
        Cs[:, t] = k & (stok == 0)
    # gecikmesi tamamen bilinen havuz dışındaki günlere düşen yapay tükenmelerin payı
    erir = [not KNOWN[p, t + 1:min(e, T)].any() for p, t, e in tuk]
    BST['yapay_tukenme'] = len(tuk); BST['havuz_disinda_eriyen'] = float(np.mean(erir)) if tuk else 0.0
    return Ys, Cs, S

def gurultu(C, M, tur, eta, rng):
    C = C.copy()
    if tur == 'FN':
        m = C & M & (rng.random(C.shape) < eta); C[m] = False
    else:
        m = ~C & M & (rng.random(C.shape) < eta); C[m] = True
    return C

from scipy.stats import poisson as _pois
t0 = ORIG[kat]; KEY = anahtar(t0); rng = np.random.default_rng(TOHUM + kat)
bas = time.time()
if sen.startswith('S_') or sen.startswith('N_'):
    kap = KAPPA.get(sen, 1.0)
    Ys, Cs, Skap = benzetim(kap, np.random.default_rng(TOHUM))
    Cs0 = Cs.copy(); Cgercek = Cs0
    Mall = KNOWN; Dtrue = Yn
    if sen.startswith('N_'):
        tur, eta = sen[2:4], int(sen[4:]) / 100
        Cs = gurultu(Cs, Mall, tur, eta, rng)
    Cgercek = Cs0
    Yobs, Cobs = Ys, Cs
    Mtest = KNOWN
else:
    cr = sen[2:]
    # CR5: SR3 bayrağı (yalnız açık kayıtlı sıfır stok sansürlü), örtük sıfır ve negatif stok günleri analizde kalır ve
    # sansürsüz sayılır. SR3'te bu günler analiz dışında bırakılır.
    Cobs = {'CR1': z['C1'], 'CR2': z['C2'], 'CR3': z['C3'], 'CR4': z['C1'], 'CR5': z['C3']}[cr]
    Mall = z['A3'] if cr == 'CR3' else (A & ~NEG if cr == 'CR4' else A)
    Yobs = Yn; Dtrue = Yn; Mtest = Mall
tr = slice(max(0, t0 - LTR), t0); te = slice(t0, t0 + H)
ntr = Mall[:, tr].sum(1); ytr = (Yobs * Mall)[:, tr].sum(1); nte = Mtest[:, te].sum(1)
# İleriye dönük seçim: başlangıç noktasında bilinen bilgiyle (eğitimde en az 28 geçerli gün ve en az 1 birim gözlenen satış).
# Test penceresinde gerçek değeri bilinen en az bir gün, ölçütün hesaplanabilmesi için gereklidir.
sel = (ntr >= 28) & (ytr >= 1) & (nte >= 1)
idx = np.where(sel)[0]
Y = Yobs[idx, tr]; C = Cobs[idx, tr] & Mall[idx, tr]; M = Mall[idx, tr]; K = KEY[idx, tr]
SID = pd.factorize(SID_all[idx])[0]; CID = pd.factorize(CID_all[idx])[0]; DIV = DIV_all[idx]
Mte = Mtest[idx, te]; Kte = KEY[idx, te]; Dte = (Dtrue[idx, te] * Mte)
Dtr_g = Dtrue[idx, tr] * M
HAF = np.broadcast_to(((np.arange(tr.start, tr.stop) - tr.start) // 7)[None, :], Y.shape).copy()
_cz = C & M
sonuc_ek = dict(sansurlu_gun=int(_cz.sum()), sansurlu_sifir_talep=int((_cz & (Dtrue[idx, tr] == 0)).sum()),
                sansurlu_sifir_satis=int((_cz & (Y == 0)).sum()), Dte_max=float(Dte.sum(1).max()),
                Dte_ust60=int((Dte.sum(1) > 60).sum()))
if sen.startswith('S_') or sen.startswith('N_'):
    sonuc_ek.update(yapay_tukenme=BST['yapay_tukenme'], havuz_disinda_eriyen=BST['havuz_disinda_eriyen'])
sonuc = dict(idx=idx, SID=SID, store=SID_all[idx], Dte=Dte.sum(1), Dtr=Dtr_g.sum(1), Ytr=(Y * M).sum(1), ntr=M.sum(1),
             nte=Mte.sum(1), cens_rate=_cz.sum(1) / np.maximum(M.sum(1), 1), eski_filtre=(Mte.sum(1) >= 7))
if sen.startswith('S_') or sen.startswith('N_'):
    sonuc['kap_var'] = BST['kap_var'][idx]
if sen.startswith('D_'):
    U = Mte & ~Cobs[idx, te]
    sonuc['Dte_unc'] = (Dtrue[idx, te] * U).sum(1); sonuc['nte_unc'] = U.sum(1)
haftalar = [slice(w * 7, (w + 1) * 7) for w in range(4)]
_son = np.zeros_like(M); _son[:, -28:] = M[:, -28:]
_ys = np.bincount(SID, weights=(Y * _son).sum(1)); _ns = np.bincount(SID, weights=_son.sum(1))
_ya = np.bincount(SID, weights=(Y * M).sum(1)); _na = np.bincount(SID, weights=M.sum(1))
with np.errstate(all='ignore'):
    _g = np.where((_ys > 0) & (_na > 0) & (_ns > 0), (_ys / np.maximum(_ns, 1)) / (_ya / np.maximum(_na, 1)), 1.0)
OLCEK = _g[SID]; sonuc['olcek'] = OLCEK
sonuc['Dw'] = np.stack([Dte[:, w].sum(1) for w in haftalar], 1)
# seri özellikleri: başlangıç noktasında gözlenebilen eğitim satışından
pozn = ((Y > 0) & M).sum(1)
sonuc['ADI'] = M.sum(1) / np.maximum(pozn, 1)
with np.errstate(all='ignore'):
    yp = np.where((Y > 0) & M, Y, np.nan); mu_p = np.nanmean(yp, 1); sd_p = np.nanstd(yp, 1)
sonuc['CV2'] = np.nan_to_num((sd_p / mu_p) ** 2)
modeller = {}
w2 = Mo.m2_secim(Y, C, M); sonuc['m2_w'] = w2
lam6, a6 = Mo.m6_secim(Y, C, M); sonuc['m6_alfa'] = a6
basit = {'M0': Mo.m0(Y, C, M), 'M1': Mo.m1(Y, C, M), 'M2': Mo.m2(Y, C, M, w2), 'M3': Mo.m3(Y, C, M),
         'M5': Mo.m5_km(Y, C, M), 'M6': lam6}
if sen.startswith('N_'):
    basit.pop('M0')
for ad, lam in basit.items():
    modeller[ad] = dict(tip='poisson', lam=lam)
sonuc['M3_sinir'] = int((basit['M3'] >= Mo.LG[-1] * 0.999).sum())
m4ler = {'M4': dict()}
ana = (sen == 'S_orta' and LTR == 112)
if ana or sen.startswith('N_'):
    # Etiket hatası payı a, eğitim penceresindeki bayraklı günlerden %5'lik rastgele bir denetim örnekleminde
    # (fiziksel sayım benzeri) gerçek durumun gözlenmesiyle tahmin edilir.
    _cb = np.where(C & M); _ns = max(1, int(round(0.05 * len(_cb[0]))))
    _sec = np.random.default_rng(TOHUM + 100 + kat).choice(len(_cb[0]), _ns, replace=False)
    _gc = Cgercek[idx, tr][_cb[0][_sec], _cb[1][_sec]]
    a_hat = float(np.mean(~_gc)); sonuc_ek.update(denetim_n=int(_ns), a_hat=a_hat)
    m4ler['M4R'] = dict(etiket=(a_hat, 0.0))
if ana or sen.startswith('D_'):
    m4ler['M4D'] = dict(hafta=HAF)
ZONLY = sen == 'S_ortaZ'
if ZONLY:
    # sıfır şişkin sürüm bellek yükü nedeniyle ayrı koşuda çalıştırılır ve istatistik aşamasında ana senaryoya eklenir
    m4ler = {'M4': dict(), 'M4Z': dict(sifir_sisme=DIV)}
if (sen.startswith('S_') or sen.startswith('D_')) and sen != 'S_ortaZ':
    m4ler['M4S'] = dict(cens=False)
if ana:
    m4ler.update({'M4H': dict(hiyerarsi=False), 'M4K': dict(hiyerarsi=False, kovaryat=False)})
if sen.startswith('S_') and sen != 'S_ortaZ':
    m4ler.update({'TB': dict(cens=False, _gercek=True), 'TK': dict(cens=False, _test=True)})
for ad, kw in m4ler.items():
    gercek = kw.pop('_gercek', False); testk = kw.pop('_test', False)
    t1 = time.time()
    if testk:
        fit = Mo.m4(Dte, np.zeros_like(Mte), Mte, Kte, SID, CID, cens=False, secim=False)
    elif ad in ('M4R', 'M4Z', 'M4D'):
        # sürümler M4 çözümünden başlatılır ve en çok 100 yinelemeyle çözülür
        f4 = modeller['M4']['fit']
        fit = Mo.m4(Y, C, M, K, SID, CID, bas=(f4['beta'], np.log(f4['phi'])), maxiter=100, **kw)
    else:
        fit = Mo.m4(Dtr_g if gercek else Y, C, M, K, SID, CID, **kw)
    modeller[ad] = dict(tip='m4', fit=fit, kw=kw, testk=testk)
    if ad == 'M4' and (ana or sen.startswith('N_')):
        prof = Mo.a_profili(Y, C, M, K, SID, CID, fit)
        sonuc['a_profil'] = np.array([prof[x] for x in sorted(prof)]); sonuc['a_aday'] = np.array(sorted(prof))
    for x in ('phi', 'em_tur', 'a', 'b'): sonuc[f'{ad}_{x}'] = fit[x]
    if fit['pz'] is not None: sonuc[ad + '_pz'] = np.asarray(fit['pz'])
    print(ad, 'sure', round(time.time() - t1, 1), 'phi', round(fit['phi'], 4), 'tur', fit['em_tur'], 'ab', fit['a'], fit['b'], flush=True)
Kmax = 60
ii_c, tt_c = np.where(C & M); y_c = Y[ii_c, tt_c].astype(float); D_c = Dtrue[idx, tr][ii_c, tt_c]
for ad, md in modeller.items():
    if md['tip'] == 'poisson':
        lam = md['lam']
        mtr = lam * M.sum(1); mte = lam * Mte.sum(1)
        pmf = Mo.poisson_pmf(mte, Kmax)
        pw = [Mo.poisson_pmf(lam * Mte[:, w].sum(1), 30) for w in haftalar]
        pwg = [Mo.poisson_pmf(OLCEK * lam * Mte[:, w].sum(1), 30) for w in haftalar]
        if sen.startswith('D_'): mte_u = lam * sonuc['nte_unc']
        m_c = lam[ii_c]
    else:
        fit = md['fit']; W = fit['W']; eu = W @ Mo.UG
        szs = 1.0 if fit['pz'] is None else (1 - fit['pz'][DIV])        # sıfır şişkin sürümde Poisson bileşeninin payı
        mu_tr = Mo.m4_mu(fit, K, M, SID, CID, hafta=HAF if fit['nh'] else None)
        mu_te = Mo.m4_mu(fit, Kte, Mte, SID, CID) * (szs[:, None] if np.ndim(szs) else 1.0)
        mu_tr_s = mu_tr * (szs[:, None] if np.ndim(szs) else 1.0)
        mtr = eu * mu_tr_s.sum(1); mte = eu * mu_te.sum(1)
        pmf = Mo.karisim_pmf(W, mu_te.sum(1), Kmax)
        pw = [Mo.karisim_pmf(W, mu_te[:, w].sum(1), 30) for w in haftalar]
        pwg = [Mo.karisim_pmf(W, OLCEK * mu_te[:, w].sum(1), 30) for w in haftalar]
        sonuc[ad + '_eu'] = eu
        if sen.startswith('D_'):
            U = Mte & ~Cobs[idx, te]; mte_u = eu * (mu_te * U).sum(1)
        m_c = eu[ii_c] * mu_tr[ii_c, tt_c]
    # sansürlü günlerde koşullu beklenti
    if ad in ('M0', 'M4S') or md.get('testk'):
        ed = y_c.copy()
    else:
        ed = Mo.kosullu_beklenti(y_c, m_c)
        if md['tip'] == 'm4' and md['fit']['pz'] is not None:
            q = md['fit']['pz'][DIV[ii_c]]
            ed = np.where(y_c == 0, (1 - q) * m_c, ed)       # yapısal sıfır olasılığı sıfır satışlı günde beklentiyi küçültür
        if md['tip'] == 'm4' and (md['fit']['a'] > 0):
            a_ = md['fit']['a']; p1 = np.where(y_c >= 1, np.clip(Mo.gammainc(np.maximum(y_c, 1e-12), m_c), 1e-300, 1), 1.0)
            p0 = np.exp(Mo._logpmf(y_c, m_c)); pi = (1 - a_) * p1 / ((1 - a_) * p1 + a_ * p0)
            ed = pi * ed + (1 - pi) * y_c                      # günün gerçekten sansürlü olma sonsal olasılığıyla ağırlık
    ek = np.bincount(ii_c, weights=ed - y_c, minlength=len(idx))
    sonuc[ad + '_imp'] = sonuc['Ytr'] + ek
    sonuc[ad + '_impabs'] = np.abs(sonuc[ad + '_imp'] - sonuc['Dtr'])
    sonuc[ad + '_gunabs'] = np.bincount(ii_c, weights=np.abs(ed - D_c), minlength=len(idx))
    med = _pois.ppf(0.5, np.maximum(ek, 1e-12)); med = np.where(ek <= 1e-12, 0, med)
    sonuc[ad + '_impmed'] = sonuc['Ytr'] + med; sonuc[ad + '_impmedabs'] = np.abs(sonuc[ad + '_impmed'] - sonuc['Dtr'])
    if sen.startswith('D_'):
        sonuc[ad + '_kayip'] = ek; sonuc[ad + '_te_unc'] = mte_u
    D = sonuc['Dte']; cdf = np.cumsum(pmf, 1); ks = np.arange(Kmax + 1)
    sonuc[ad + '_crps'] = ((cdf - (ks[None, :] >= D[:, None])) ** 2).sum(1)
    q10 = (cdf < 0.1).sum(1); q90 = (cdf < 0.9).sum(1)
    sonuc[ad + '_pin90'] = np.where(D >= q90, 0.9 * (D - q90), 0.1 * (q90 - D))
    sonuc[ad + '_trabs'] = np.abs(mtr - sonuc['Dtr']); sonuc[ad + '_tr'] = mtr; sonuc[ad + '_te'] = mte
    sonuc[ad + '_cov80'] = ((D >= q10) & (D <= q90)).astype(float); sonuc[ad + '_wid80'] = (q90 - q10).astype(float)
    sonuc[ad + '_pit'] = np.take_along_axis(cdf, np.minimum(D, Kmax).astype(int)[:, None], 1)[:, 0]
    # karar katmanı
    for cr in CRS:
        p_ = cr / (1 - cr); cost = np.zeros(len(D)); stok = np.zeros(len(D)); satilan = np.zeros(len(D))
        costd = np.zeros(len(D)); I = np.zeros(len(D))
        for w in range(4):
            S = (np.cumsum(pw[w], 1) < cr).sum(1).astype(float); Dw = sonuc['Dw'][:, w]
            cost += np.maximum(S - Dw, 0) + p_ * np.maximum(Dw - S, 0); stok += S; satilan += np.minimum(S, Dw)
            # devirli: hafta sonu kalan stok sonraki haftaya geçer, stok aşağı çekilemez
            pozisyon = np.maximum(S, I); sat = np.minimum(pozisyon, Dw); I = pozisyon - sat
            costd += I + p_ * (Dw - sat)
        sonuc[f'{ad}_cost{int(cr*100)}'] = cost; sonuc[f'{ad}_stok{int(cr*100)}'] = stok; sonuc[f'{ad}_sat{int(cr*100)}'] = satilan
        sonuc[f'{ad}_costd{int(cr*100)}'] = costd
        cost = np.zeros(len(D))
        for w in range(4):
            S = (np.cumsum(pwg[w], 1) < cr).sum(1).astype(float); Dw = sonuc['Dw'][:, w]
            cost += np.maximum(S - Dw, 0) + p_ * np.maximum(Dw - S, 0)
        sonuc[f'{ad}_costg{int(cr*100)}'] = cost
sonuc.update(sonuc_ek)
os.makedirs(os.path.join(out, 'deney'), exist_ok=True)
np.savez_compressed(os.path.join(out, 'deney', f'{sen}_k{kat}' + ('' if LTR == 112 else f'_L{LTR}') + '.npz'),
                    **{k: np.asarray(v) for k, v in sonuc.items()})
gm = _cz.sum() / M.sum(); lost = 1 - (Y * M).sum() / max(Dtr_g.sum(), 1)
print(sen, kat, 'seri', len(idx), 'sansur', round(float(gm), 4), 'kayip_pay', round(float(lost), 4), 'sure', round(time.time() - bas, 1),
      {ad: (round(float((sonuc[ad + '_imp'].sum() - sonuc['Dtr'].sum()) / sonuc['Dtr'].sum()), 4),
            round(float(sonuc[ad + '_impabs'].sum() / sonuc['Dtr'].sum()), 4)) for ad in modeller}, flush=True)
