# -*- coding: utf-8 -*-
"""Deney çıktılarının özetlenmesi: hata ölçütleri, ortak indeksli hiyerarşik eşleştirilmiş önyükleme, Holm düzeltmesi,
kıyas sapmasının ayrıştırılması, karar katmanı ve heterojenlik çözümlemesi.
Kullanım: python3 -I istatistik.py <cikti_klasor>"""
import sys, os, json
import numpy as np
import statsmodels.api as sm
out = sys.argv[1]; D = os.path.join(out, 'deney')
B = 1000; TOHUM = 20260427
MODELLER = ['M0', 'M1', 'M2', 'M3', 'M5', 'M6', 'M4', 'M4R', 'M4Z', 'M4D', 'M4S', 'M4H', 'M4K', 'TB', 'TK']
CRS = [50, 75, 90, 95]


def yukle(sen, son=''):
    parts = []
    for k in range(4):
        f = os.path.join(D, f'{sen}_k{k}{son}.npz')
        if not os.path.exists(f): continue
        p = dict(np.load(f))
        if sen == 'S_orta' and not son and os.path.exists(os.path.join(D, f'S_ortaZ_k{k}.npz')):
            zr = dict(np.load(os.path.join(D, f'S_ortaZ_k{k}.npz')))
            if np.array_equal(zr['idx'], p['idx']):
                for x in zr:
                    if x.startswith('M4Z'): p[x] = zr[x]
        if sen.startswith('N_') or son:
            ref = dict(np.load(os.path.join(D, f'S_orta_k{k}.npz')))
            if np.array_equal(ref['idx'], p['idx']):
                for x in ref:
                    if x.startswith(('TB_', 'TK_')) and x not in p: p[x] = ref[x]
        parts.append((k, p))
    if not parts: return None
    n0 = len(parts[0][1]['idx'])
    keys = [x for x in parts[0][1] if parts[0][1][x].ndim >= 1 and len(parts[0][1][x]) == n0 and all(x in p for _, p in parts)]
    r = {x: np.concatenate([p[x] for _, p in parts]) for x in keys}
    r['kat'] = np.concatenate([np.full(len(p['idx']), k) for k, p in parts])
    r['skaler'] = {k: {x: p[x].item() for x in p if p[x].ndim == 0} for k, p in parts}
    r['vektor'] = {k: {x: p[x].tolist() for x in p if p[x].ndim == 1 and len(p[x]) != len(p['idx'])} for k, p in parts}
    r['katlar'] = [k for k, _ in parts]
    return r


def agirliklar(r, rng):
    """Ortak önyükleme ağırlıkları (B x n). Önce mağazalar, sonra seçilen her mağaza içinde seriler yerine koymalı
    çekilir. Bir serinin bütün başlangıç noktalarındaki gözlemleri birlikte taşınır. Bütün karşılaştırmalarda aynı
    ağırlık matrisi kullanılır."""
    st = r['store']; sid = r['idx']
    useri, inv = np.unique(sid, return_inverse=True)
    smag = np.array([st[inv == j][0] for j in range(len(useri))])
    mags = np.unique(smag); mser = {m: np.where(smag == m)[0] for m in mags}
    W = np.zeros((B, len(useri)), np.float32)
    for b in range(B):
        for m in rng.choice(mags, len(mags)):
            s = mser[m]; np.add.at(W[b], rng.choice(s, len(s)), 1)
    return W[:, inv]


def oran(W, pay, payda):
    return (W @ pay) / (W @ payda)


def gerekli(r, m):
    return all(f'{m}_{x}' in r for x in ('imp', 'te'))


def olcutler(r, m, s=None):
    s = np.ones(len(r['idx']), bool) if s is None else s
    Dtr, Dte = r['Dtr'][s], r['Dte'][s]
    o = dict(n=int(s.sum()),
             gk_yanlilik=(r[m + '_imp'][s].sum() - Dtr.sum()) / Dtr.sum(),
             gk_wape=r[m + '_impabs'][s].sum() / Dtr.sum(),
             gk_wape_medyan=r[m + '_impmedabs'][s].sum() / Dtr.sum(),
             gk_gun_wape=r[m + '_gunabs'][s].sum() / Dtr.sum(),
             duzey_yanlilik=(r[m + '_tr'][s].sum() - Dtr.sum()) / Dtr.sum(),
             t_yanlilik=(r[m + '_te'][s].sum() - Dte.sum()) / Dte.sum(),
             t_wape=np.abs(r[m + '_te'][s] - Dte).sum() / Dte.sum(),
             crps=r[m + '_crps'][s].mean(), kapsama80=r[m + '_cov80'][s].mean(), genislik80=r[m + '_wid80'][s].mean(),
             pinball90=r[m + '_pin90'][s].mean())
    if 'TB_te' in r:
        o['kiyas_sapma'] = np.abs(r[m + '_te'][s] - r['TB_te'][s]).sum() / r['TB_te'][s].sum()
        o['kiyas_yon'] = (r[m + '_te'][s].sum() - r['TB_te'][s].sum()) / r['TB_te'][s].sum()
    dw = r['Dw'][s].sum()
    for cr in CRS:
        o[f'maliyet{cr}'] = r[f'{m}_cost{cr}'][s].sum() / Dte.sum()
        o[f'maliyetd{cr}'] = r[f'{m}_costd{cr}'][s].sum() / Dte.sum()
        o[f'karsilama{cr}'] = r[f'{m}_sat{cr}'][s].sum() / dw
        o[f'stok{cr}'] = r[f'{m}_stok{cr}'][s].sum() / dw
        for ref in ('TB', 'TK'):
            if f'{ref}_cost{cr}' in r:
                o[f'pisman_{ref}{cr}'] = (r[f'{m}_cost{cr}'][s].sum() - r[f'{ref}_cost{cr}'][s].sum()) / Dte.sum()
                o[f'pismand_{ref}{cr}'] = (r[f'{m}_costd{cr}'][s].sum() - r[f'{ref}_costd{cr}'][s].sum()) / Dte.sum()
                o[f'pismang_{ref}{cr}'] = (r[f'{m}_costg{cr}'][s].sum() - r[f'{ref}_costg{cr}'][s].sum()) / Dte.sum()
        # sıfır stok politikası: bütün talep kaybedilir, maliyet = p * talep, talep başına p
        o[f'sifir_stok{cr}'] = cr / (100 - cr)
    return o


# önyüklenebilir ölçütler: her biri (pay, payda) çifti veya ortalama
def bo_vektor(r, m, olcut):
    if olcut == 'gk_wape': return r[m + '_impabs'], r['Dtr']
    if olcut == 'gk_wape_medyan': return r[m + '_impmedabs'], r['Dtr']
    if olcut == 'gk_gun_wape': return r[m + '_gunabs'], r['Dtr']
    if olcut == 'gk_yanlilik': return r[m + '_imp'] - r['Dtr'], r['Dtr']
    if olcut == 'kiyas_sapma': return np.abs(r[m + '_te'] - r['TB_te']), r['TB_te']
    if olcut == 'crps': return r[m + '_crps'], np.ones(len(r['idx']))
    if olcut == 'maliyet90': return r[m + '_cost90'], r['Dte']
    if olcut == 'maliyetd90': return r[m + '_costd90'], r['Dte']
    if olcut == 't_wape': return np.abs(r[m + '_te'] - r['Dte']), r['Dte']
    raise KeyError(olcut)


def boot_tek(r, W, m, olcut):
    a, b = bo_vektor(r, m, olcut); v = a.sum() / b.sum(); bs = oran(W, a, b)
    return dict(deger=float(v), alt=float(np.percentile(bs, 2.5)), ust=float(np.percentile(bs, 97.5)))


def boot_fark(r, W, a, b, olcut, mutlak=False):
    pa, qa = bo_vektor(r, a, olcut); pb, qb = bo_vektor(r, b, olcut)
    f = lambda x: np.abs(x) if mutlak else x
    base = f(pa.sum() / qa.sum()) - f(pb.sum() / qb.sum())
    bs = f(oran(W, pa, qa)) - f(oran(W, pb, qb))
    k = min((bs <= 0).sum(), (bs >= 0).sum())
    p = min(1.0, 2 * (k + 1) / (B + 1))
    return dict(fark=float(base), alt=float(np.percentile(bs, 2.5)), ust=float(np.percentile(bs, 97.5)), p=float(p))


def holm(ps):
    ps = np.asarray(ps); o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0
    for k, i in enumerate(o):
        run = max(run, (m - k) * ps[i]); adj[i] = min(1, run)
    return adj


def karsilastir(r, W, hedef, rakipler, olcutler_):
    kars = {}
    for ad in olcutler_:
        mutlak = ad == 'gk_yanlilik'
        rows = {b: boot_fark(r, W, hedef, b, ad, mutlak=mutlak) for b in rakipler if gerekli(r, b)}
        adj = holm([v['p'] for v in rows.values()])
        for (b, v), a in zip(rows.items(), adj): v['p_holm'] = float(a)
        kars[ad + ('_mutlak' if mutlak else '')] = rows
    return kars


sonuc = {}
rng = np.random.default_rng(TOHUM)
# 1) yeniden sansürleme senaryoları
for sen in ['S_dusuk', 'S_orta', 'S_yuksek']:
    r = yukle(sen)
    if r is None: continue
    ms = [m for m in MODELLER if gerekli(r, m)]
    W = agirliklar(r, rng)
    gd = {}
    for k in r['katlar']:
        s = r['kat'] == k
        gd[int(k)] = float((r['Dte'][s].sum() / r['nte'][s].sum()) / (r['Dtr'][s].sum() / r['ntr'][s].sum()) - 1)
    sk = r['skaler']
    sonuc[sen] = dict(n_gozlem=int(len(r['idx'])), n_seri=int(len(np.unique(r['idx']))), katlar=r['katlar'],
                      n_magaza=int(len(np.unique(r['store']))),
                      sansur_orani=float(np.average(r['cens_rate'], weights=r['ntr'])),
                      kayip_payi=float(1 - r['Ytr'].sum() / r['Dtr'].sum()),
                      Dtr=float(r['Dtr'].sum()), Dte=float(r['Dte'].sum()),
                      eski_filtre_n=int(r['eski_filtre'].sum()),
                      kap_varsayilan=int(r['kap_var'].sum()) if 'kap_var' in r else None,
                      sansurlu_gun=int(sum(v['sansurlu_gun'] for v in sk.values())),
                      sansurlu_sifir_satis=int(sum(v['sansurlu_sifir_satis'] for v in sk.values())),
                      sansurlu_sifir_talep=int(sum(v['sansurlu_sifir_talep'] for v in sk.values())),
                      yapay_tukenme=int(sum(v.get('yapay_tukenme', 0) for v in sk.values())),
                      havuz_disinda_eriyen={int(k): v.get('havuz_disinda_eriyen') for k, v in sk.items()},
                      Dte_ust60=int(sum(v['Dte_ust60'] for v in sk.values())),
                      M3_sinir=int(sum(v['M3_sinir'] for v in sk.values())),
                      olcut={m: olcutler(r, m) for m in ms},
                      ci={m: {o: boot_tek(r, W, m, o) for o in ('gk_yanlilik', 'gk_wape', 'gk_wape_medyan', 'kiyas_sapma', 'crps', 'maliyet90')}
                          for m in ms},
                      kat_olcut={int(k): {m: olcutler(r, m, r['kat'] == k) for m in ms} for k in r['katlar']},
                      skaler=sk, gunluk_degisim=gd,
                      m6_alfa={int(k): v.get('m6_alfa') for k, v in sk.items()},
                      m2_w={int(k): v.get('m2_w') for k, v in sk.items()})
    if sen != 'S_orta': continue
    R = sonuc['S_orta']
    R['eski_filtre'] = {m: olcutler(r, m, r['eski_filtre']) for m in ms}
    rak = ['M0', 'M1', 'M2', 'M3', 'M5', 'M6', 'M4S', 'M4H', 'M4K', 'M4Z', 'M4D']   # gürültüsüz senaryoda a = 0 olduğu için M4R aileden çıkarılır
    R['karsilastirma'] = karsilastir(r, W, 'M4', rak, ['gk_wape', 'gk_wape_medyan', 'gk_yanlilik', 'kiyas_sapma', 'crps', 'maliyet90'])
    # kıyas sapmasının ayrıştırılması: M0 -> M4S mimari katkı, M4S -> M4 sansür düzeltmesi katkısı
    ks = {m: bo_vektor(r, m, 'kiyas_sapma') for m in ('M0', 'M4S', 'M4')}
    v = {m: ks[m][0].sum() / ks[m][1].sum() for m in ks}; bsv = {m: oran(W, *ks[m]) for m in ks}
    top = v['M0'] - v['M4']; mim = v['M0'] - v['M4S']; san = v['M4S'] - v['M4']
    bpay = (bsv['M0'] - bsv['M4S']) / (bsv['M0'] - bsv['M4'])
    R['ks_ayristirma'] = dict(M0=v['M0'], M4S=v['M4S'], M4=v['M4'], toplam=top, mimari=mim, sansur=san,
                              mimari_pay=mim / top, sansur_pay=san / top,
                              mimari_pay_alt=float(np.percentile(bpay, 2.5)), mimari_pay_ust=float(np.percentile(bpay, 97.5)),
                              sansur_marjinal=san / v['M4S'])
    # heterojenlik: seri düzeyinde M4'ün M0'a göre mutlak geri kazanım hatası azalışı (birim).
    # Açıklayıcılar yalnız başlangıç noktasında gözlenebilen eğitim satışı ve bayraktan türetilir.
    y = r['M0_impabs'] - r['M4_impabs']
    X = sm.add_constant(np.column_stack([np.log(r['ADI']), r['CV2'], r['cens_rate'], np.log1p(r['Ytr'])]))
    fit = sm.OLS(y, X).fit(cov_type='cluster', cov_kwds={'groups': r['store']})
    R['heterojenlik'] = dict(ad=['sabit', 'log_OTA', 'DK2', 'bayrak_orani', 'log1p_gozlenen_satis'],
                             katsayi=fit.params.tolist(), se=fit.bse.tolist(), p=fit.pvalues.tolist(), n=int(fit.nobs), r2=float(fit.rsquared),
                             y_ort=float(y.mean()))
    # sansür oranı dilimleri (sıfır dilimi dahil)
    cr_ = r['cens_rate']; pos = cr_[cr_ > 0]
    q = np.quantile(pos, [0.5, 0.8]) if len(pos) else [0, 0]
    dil = []
    for a, b, et in [(0, 0, '0'), (0, q[0], 'd1'), (q[0], q[1], 'd2'), (q[1], 1.0, 'd3')]:
        s = (cr_ == 0) if et == '0' else ((cr_ > a) & (cr_ <= b))
        dil.append(dict(alt=float(a), ust=float(b), n=int(s.sum()), n_sansurlu_gun=int(np.round((cr_[s] * r['ntr'][s]).sum())),
                        **{m: dict(gk_yanlilik=olcutler(r, m, s)['gk_yanlilik'], gk_wape=olcutler(r, m, s)['gk_wape'],
                                   gk_wape_medyan=olcutler(r, m, s)['gk_wape_medyan'])
                           for m in ['M0', 'M1', 'M2', 'M3', 'M5', 'M6', 'M4', 'M4S', 'TB']}))
    R['sansur_dilim'] = dil
    # OTA dilimleri (kesikli talep sınıfları için Syntetos-Boylan eşiği 1,32)
    dil = []
    for a, b in [(0, 1.32), (1.32, 30), (30, 60), (60, 1e9)]:
        s = (r['ADI'] > a) & (r['ADI'] <= b)
        if s.sum() == 0: continue
        dil.append(dict(alt=a, ust=b, n=int(s.sum()),
                        **{m: dict(gk_yanlilik=olcutler(r, m, s)['gk_yanlilik'], gk_wape=olcutler(r, m, s)['gk_wape'])
                           for m in ['M0', 'M1', 'M2', 'M4', 'M4Z', 'M4S'] if gerekli(r, m)}))
    R['ota_dilim'] = dil
    R['pit'] = {m: np.histogram(r[m + '_pit'], bins=10, range=(0, 1))[0].tolist() for m in ['M0', 'M1', 'M2', 'M4', 'M4S', 'M6', 'TB', 'TK']}
    R['tahmin_parametre'] = {m: {x: [sk[k].get(f'{m}_{x}') for k in r['katlar']] for x in ('phi', 'em_tur', 'a', 'b')}
                             for m in ms if f'{m}_phi' in sk[r['katlar'][0]]}
    R['M4Z_pz'] = {int(k): r['vektor'][k].get('M4Z_pz') for k in r['katlar']}
    R['a_profil'] = {int(k): r['vektor'][k].get('a_profil') for k in r['katlar']}
    R['a_hat'] = {int(k): sk[k].get('a_hat') for k in r['katlar']}
# 2) gürültü senaryoları
gur = {}
for tur in ['FN', 'FP']:
    for eta in ['05', '10', '20']:
        r = yukle(f'N_{tur}{eta}')
        if r is None: continue
        ms = [m for m in ['M1', 'M2', 'M3', 'M5', 'M6', 'M4', 'M4R'] if gerekli(r, m)]
        gur[f'{tur}{eta}'] = {m: olcutler(r, m) for m in ms}
        gur[f'{tur}{eta}']['M4R_ab'] = {int(k): (v.get('M4R_a'), v.get('M4R_b')) for k, v in r['skaler'].items()}
        gur[f'{tur}{eta}']['a_hat'] = {int(k): v.get('a_hat') for k, v in r['skaler'].items()}
        gur[f'{tur}{eta}']['a_profil'] = {int(k): r['vektor'][k].get('a_profil') for k in r['katlar']}
        gur[f'{tur}{eta}']['sansur_orani'] = float(np.average(r['cens_rate'], weights=r['ntr']))
        if tur == 'FP' and eta == '20':
            W = agirliklar(r, rng)
            gur['FP20_fark'] = {o: boot_fark(r, W, 'M4R', 'M4', o, mutlak=(o == 'gk_yanlilik')) for o in ('gk_yanlilik', 'gk_wape')}
sonuc['gurultu'] = gur
# 3) doğal veri
for cr in ['CR1', 'CR2', 'CR3', 'CR4', 'CR5']:
    r = yukle(f'D_{cr}')
    if r is None: continue
    ms = [m for m in ['M0', 'M1', 'M2', 'M3', 'M5', 'M6', 'M4', 'M4R', 'M4Z', 'M4D', 'M4S'] if gerekli(r, m)]
    W = agirliklar(r, rng)
    o = {}
    for m in ms:
        Dte = r['Dte']; Du = r['Dte_unc']
        o[m] = dict(t_yanlilik_satis=(r[m + '_te'].sum() - Dte.sum()) / Dte.sum(),
                    t_wape_satis=np.abs(r[m + '_te'] - Dte).sum() / Dte.sum(), crps_satis=r[m + '_crps'].mean(),
                    t_yanlilik_stoklu=(r[m + '_te_unc'].sum() - Du.sum()) / Du.sum(),
                    t_wape_stoklu=np.abs(r[m + '_te_unc'] - Du).sum() / Du.sum(),
                    egitim_duzey=r[m + '_tr'].sum() / r['Ytr'].sum() - 1)
        if m not in ('M0', 'M4S'):
            kp = r[m + '_imp'] - r['Ytr']; Y = r['Ytr']; bs = oran(W, kp, Y)
            o[m]['kayip_talep_orani'] = dict(deger=float(kp.sum() / Y.sum()), alt=float(np.percentile(bs, 2.5)), ust=float(np.percentile(bs, 97.5)))
    sk = r['skaler']
    sonuc[f'D_{cr}'] = dict(n_gozlem=int(len(r['idx'])), n_seri=int(len(np.unique(r['idx']))),
                            n_gozlem_kat={int(k): int((r['kat'] == k).sum()) for k in r['katlar']},
                            sansur_orani=float(np.average(r['cens_rate'], weights=r['ntr'])),
                            Ytr=float(r['Ytr'].sum()), Dte=float(r['Dte'].sum()), Dte_unc=float(r['Dte_unc'].sum()),
                            sansurlu_gun=int(sum(v['sansurlu_gun'] for v in sk.values())),
                            sansurlu_sifir_satis=int(sum(v['sansurlu_sifir_satis'] for v in sk.values())),
                            M3_sinir=int(sum(v['M3_sinir'] for v in sk.values())),
                            olcut=o, skaler=sk,
                            eski_filtre_n=int(r['eski_filtre'].sum()))
# 4) pencere duyarlılığı
for L in ['56', '999']:
    r = yukle('S_orta', f'_L{L}')
    if r is None: continue
    sonuc[f'S_orta_L{L}'] = dict(n_gozlem=int(len(r['idx'])), sansur_orani=float(np.average(r['cens_rate'], weights=r['ntr'])),
                                 olcut={m: olcutler(r, m) for m in MODELLER if gerekli(r, m)})


def temiz(o):
    if isinstance(o, dict): return {str(k): temiz(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [temiz(v) for v in o]
    if isinstance(o, (np.floating, float)): return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, np.ndarray): return temiz(o.tolist())
    return o


json.dump(temiz(sonuc), open(os.path.join(out, 'sonuclar.json'), 'w'), ensure_ascii=False, indent=1)
print('tamam', list(sonuc.keys()))
