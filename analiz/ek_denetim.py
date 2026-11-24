import sys, json, numpy as np
out = sys.argv[1]
z = np.load(out + '/panel_ham.npz'); OH = z['OH'].astype(np.int32); G = z['G']; R = z['R']
p = np.load(out + '/panel.npz'); A = p['A']; IMP = p['IMP']; NEG = p['NEG']; C1 = p['C1']
P, T = OH.shape; has = OH != -999
anyrec = has.any(1); first = np.where(anyrec, has.argmax(1), T); last = np.where(anyrec, T - 1 - has[:, ::-1].argmax(1), -1)
ended = anyrec & (last < T - 1)
idx = np.arange(T)[None, :]
term = np.zeros_like(IMP); r = np.where(ended)[0]; term[r, last[r] + 1] = True
term &= IMP
inner = IMP & ~term
res = dict(ortuk=int(IMP.sum()), ortuk_terminal=int(term.sum()), ortuk_ic=int(inner.sum()))
# iç boşluk dizileri: başlangıç günü = inner & önceki gün kayıtlı
st = inner.copy(); st[:, 1:] = inner[:, 1:] & has[:, :-1]; st[:, 0] = False
rr, cc = np.where(st)
onceki = OH[rr, cc - 1]
res['ic_bosluk_sayisi'] = int(len(rr))
res['ic_bosluk_onceki_deger'] = {str(k): int(v) for k, v in zip(*np.unique(np.clip(onceki, -1, 3), return_counts=True))}
ilk_satis = G[rr, cc] > 0
res['ic_bosluk_ilk_gun_satis_orani'] = float(ilk_satis.mean())
for v in (0, 1):
    m = onceki == v; res[f'ic_bosluk_onceki{v}_n'] = int(m.sum()); res[f'ic_bosluk_onceki{v}_ilk_gun_satis'] = float(ilk_satis[m].mean())
m = onceki >= 2; res['ic_bosluk_onceki2plus_n'] = int(m.sum()); res['ic_bosluk_onceki2plus_ilk_gun_satis'] = float(ilk_satis[m].mean())
# boşluk süreleri
L = []
for a, b in zip(rr, cc):
    e = b
    while e < T and inner[a, e]: e += 1
    L.append(e - b)
L = np.array(L); res['ic_bosluk_sure_medyan'] = float(np.median(L)); res['ic_bosluk_sure_ort'] = float(L.mean())
# boşluk sonrası kayıt değeri
son = [OH[a, b + l] if b + l < T else -999 for a, b, l in zip(rr, cc, L)]
son = np.array(son); res['ic_bosluk_sonrasi_pozitif_oran'] = float((son > 0).mean())
# terminal örtük sıfırlar: ertesi gün satış yok olanlar
rt, ct = np.where(term)
lq = OH[rt, ct - 1]; sat = G[rt, ct] > 0
res['terminal_satissiz'] = int((~sat).sum()); res['terminal_satisli'] = int(sat.sum())
res['terminal_satissiz_son1'] = int(((lq == 1) & ~sat).sum()); res['terminal_satissiz_son2plus'] = int(((lq >= 2) & ~sat).sum()); res['terminal_satissiz_son0'] = int(((lq == 0) & ~sat).sum())
res['terminal_satissiz_negatif'] = int(((lq < 0) & ~sat).sum())
# sansürlü günlerin örtük sıfır payı
res['CR1_sansur'] = int(C1.sum()); res['CR1_ortuk'] = int((C1 & IMP).sum()); res['CR1_negatif'] = int((C1 & NEG).sum())
# birim muhasebesi
res['pozitif_birim_toplam'] = float(G.sum()); res['pozitif_satis_seri_gun_tum'] = int((G > 0).sum())
res['pozitif_satis_seri_gun_etkin'] = int((A & (G > 0)).sum()); res['etkin_birim'] = float(G[A].sum())
res['ayni_gun_coklu_satis_seri_gun'] = int((G > 1).sum())
both = has[:, 1:] & has[:, :-1]; net = (G - R)[:, 1:]
res['ardisik_kayitli_net_satis_gun'] = int((both & (net != 0)).sum())
res['ardisik_kayitli_net_negatif'] = int((both & (net < 0)).sum())
res['ardisik_kayitli_iade_olan'] = int((both & (R[:, 1:] > 0)).sum())
dl = -(OH[:, 1:] - OH[:, :-1])
mm = both & (net != 0)
res['ardisik_eslesmeyen'] = int((mm & (dl != net)).sum()); res['ardisik_eslesmeyen_stok_artisi'] = int((mm & (dl != net) & (dl < 0)).sum())
# aynı ve önceki gün birlikte eşleşme
prev = (G - R)[:, :-1]
ok1 = mm & (dl == net); ok0 = mm & (dl == prev)
res['iki_kosul_birlikte'] = int((ok1 & ok0).sum())
json.dump(res, open(sys.argv[2], 'w'), indent=1); print(json.dumps(res, indent=1))
# SR4: SR1 bayrağı, negatif stok günleri dışarıda
A4 = A & ~NEG; C4 = C1 & A4; Y = p['Y']; sg = A4 & (Y > 0)
res['CR4'] = dict(gun=int(A4.sum()), sansurlu_gun=int(C4.sum()), oran=float(C4.sum() / A4.sum()),
                  satis_gunu_sansurlu=float((C4 & sg).sum() / sg.sum()), birim_sansurlu=float(Y[C4].sum() / Y[A4].sum()))
# aynı payda üzerinde iki eşleşme koşulu (ardışık kayıtlı ve aynı gün net satışı sıfırdan farklı günler)
res['payda_ayni_gun'] = int(mm.sum()); res['ayni_gun_esles_ayni_payda'] = float(ok1.sum() / mm.sum())
res['onceki_gun_esles_ayni_payda'] = float(ok0.sum() / mm.sum()); res['iki_kosul_pay'] = float((ok1 & ok0).sum() / mm.sum())
res['yalniz_onceki_gun'] = int((ok0 & ~ok1).sum())
# iadeler: etkin pencerede iade bulunan seri-gün payı ve iade biriminin satış birimine oranı
res['iade_seri_gun'] = int((A & (R > 0)).sum()); res['iade_seri_gun_payi'] = float((A & (R > 0)).sum() / A.sum())
res['iade_birim_etkin'] = float(R[A].sum()); res['iade_birim_orani'] = float(R[A].sum() / G[A].sum())
C5 = p['C3'] & A; sg5 = A & (Y > 0)
res['CR5'] = dict(gun=int(A.sum()), sansurlu_gun=int(C5.sum()), oran=float(C5.sum() / A.sum()),
                  satis_gunu_sansurlu=float((C5 & sg5).sum() / sg5.sum()), birim_sansurlu=float(Y[C5].sum() / Y[A].sum()))
res['terminal_satissiz_dusus'] = res['terminal_satissiz_son1'] + res['terminal_satissiz_son2plus']
res['terminal_satissiz_dusus_pay_CR1'] = res['terminal_satissiz_dusus'] / res['CR1_sansur']
json.dump(res, open(sys.argv[2], 'w'), indent=1); print(res['CR4'], res['terminal_satissiz_dusus'], res['terminal_satissiz_dusus_pay_CR1'])
