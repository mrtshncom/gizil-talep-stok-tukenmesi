# -*- coding: utf-8 -*-
"""Talep modelleri. Bütün modeller aynı girdiyi alır:
Y (n x t) gözlenen satış, C (n x t) sansür riski bayrağı, M (n x t) analize giren gün, KEY (n x t) gün, fiyat durumu ve
ürün yaşı kodu, SID (n,) mağaza kodu, CID (n,) alt kategori kodu.
Basit modeller seri başına sabit günlük talep düzeyi döndürür. M4 ailesi seri çarpanının sonsal ağırlıklarını (W) ve
ortak katsayıları döndürür."""
import numpy as np
from scipy.special import gammainc, gammaln


def logsumexp(a, axis=1):
    """Satır bazında log toplam üstel (iki boyutlu dizi, axis=1)."""
    m = a.max(axis=1, keepdims=True)
    m = np.where(np.isfinite(m), m, 0.0)
    return np.log(np.exp(a - m).sum(axis=1)) + m[:, 0]
from scipy.optimize import minimize, minimize_scalar
from scipy.stats import gamma as gamma_dist

# Seri çarpanı ızgarası: [1e-4, 1e2] aralığında logaritmik aralıklı 501 nokta. Önsel ağırlıklar her noktanın hücresine düşen
# gama olasılık kütlesidir (hücre sınırları ardışık noktaların geometrik ortası, ilk hücre 0'dan, son hücre sonsuza uzanır).
UG = np.exp(np.linspace(np.log(1e-4), np.log(1e2), 501))
_SINIR = np.r_[0.0, np.sqrt(UG[1:] * UG[:-1]), np.inf]
LG = np.exp(np.linspace(np.log(1e-5), np.log(5.0), 401))   # M3 için günlük talep ızgarası
NK = 7 * 5 * 6                                              # gün x fiyat durumu x ürün yaşı
PHI_ARALIK = (1e-3, 50.0)                                   # dağılım parametresinin sürekli arama aralığı


def _logsf(y, m):
    """log P(D >= y), D ~ Poisson(m), y >= 1."""
    return np.log(np.clip(gammainc(y, m), 1e-300, 1.0))


def _logpmf(y, m):
    return y * np.log(np.maximum(m, 1e-300)) - m - gammaln(y + 1)


def kosullu_beklenti(y, m):
    """Poisson(m) için E[D | D >= y]. y = 0 iken m, y >= 1 iken m P(D >= y-1) / P(D >= y)."""
    m = np.maximum(m, 1e-12)
    ust = lambda k: np.where(k <= 0, 1.0, gammainc(np.maximum(k, 1e-12), m))
    r = m * ust(y - 1) / np.maximum(ust(y), 1e-300)
    r = np.where(ust(y) < 1e-200, y + m, r)
    return np.maximum(np.where(y >= 1, r, m), y)


# ---------------------------------------------------------------- basit modeller
def m0(Y, C, M):
    """Satışı talep sayan model."""
    n = M.sum(1)
    return np.where(n > 0, (Y * M).sum(1) / np.maximum(n, 1), 0.0)


def m1(Y, C, M):
    """Sansür riskli günleri silen model. Sansürsüz günü olmayan seride M0 değeri kullanılır."""
    U = M & ~C
    n = U.sum(1)
    return np.where(n > 0, (Y * U).sum(1) / np.maximum(n, 1), m0(Y, C, M))


def m2(Y, C, M, w):
    """Kayan profil ile atama: sansürlü günde talep, son w takvim günündeki sansürsüz günlerin ortalaması ile satışın
    büyüğüdür. Son w günde sansürsüz gün yoksa serinin M1 düzeyi kullanılır (geri dönüş kuralı)."""
    U = (M & ~C).astype(np.float64)
    cy = np.cumsum(np.pad(Y * U, ((0, 0), (1, 0))), axis=1)
    cn = np.cumsum(np.pad(U, ((0, 0), (1, 0))), axis=1)
    t = Y.shape[1]; hi = np.arange(t); lo = np.maximum(hi - w, 0)
    sy = cy[:, hi] - cy[:, lo]; sn = cn[:, hi] - cn[:, lo]
    yedek = m1(Y, C, M)[:, None]
    prof = np.where(sn > 0, sy / np.maximum(sn, 1), yedek)
    Dh = np.where(C & M, np.maximum(Y, prof), Y)
    n = M.sum(1)
    return np.where(n > 0, (Dh * M).sum(1) / np.maximum(n, 1), 0.0)


def censored_ll_const(Y, C, M, lam):
    m = np.maximum(lam, 1e-6)[:, None] * np.ones_like(Y)
    unc = M & ~C; cen = M & C & (Y >= 1)
    return _logpmf(Y[unc], m[unc]).sum() + _logsf(Y[cen], m[cen]).sum()


def m2_secim(Y, C, M, val=28, adaylar=(14, 28, 56)):
    """M2 pencere uzunluğu, eğitim penceresinin son val günü üzerinde gözlenebilir sansürlü olabilirlikle seçilir.
    Sansürlü olabilirlik burada yalnızca adaylar arasında bir sıralama ölçütü olarak kullanılır."""
    t = Y.shape[1]; a = t - val
    en_iyi, skor = None, -np.inf
    for w in adaylar:
        lam = m2(Y[:, :a], C[:, :a], M[:, :a], w)
        ll = censored_ll_const(Y[:, a:], C[:, a:], M[:, a:], lam)
        if ll > skor: en_iyi, skor = w, ll
    return en_iyi


def m3(Y, C, M):
    """Seri başına sansürlü Poisson en çok olabilirlik. Sansürsüz günü olmayan ve sansürlü günleri pozitif satışlı seride
    olabilirlik monoton arttığı için tahmin ızgaranın üst sınırına (günde 5 birim) yerleşir."""
    unc = M & ~C; cen = M & C & (Y >= 1)
    n_u = unc.sum(1); s_u = (Y * unc).sum(1)
    ll = s_u[:, None] * np.log(LG)[None, :] - n_u[:, None] * LG[None, :]
    ii, tt = np.where(cen)
    if len(ii):
        np.add.at(ll, ii, _logsf(Y[ii, tt][:, None], LG[None, :]))
    lam = LG[ll.argmax(1)]
    return np.where((s_u + (Y * cen).sum(1)) == 0, 0.0, lam)


def m5_km(Y, C, M, kmax=63):
    """Seri içi Kaplan-Meier: günlük talebin sağdan sansürlü dağılımı. Sansürlü ve satışı y olan gün D > y - 1 bilgisini
    taşır ve y - 1 değerine kadar risk kümesinde kalır. Sıfır satışlı sansürlü gün bilgi taşımaz. Ortalama, hayatta kalma
    fonksiyonunun en büyük gözleme kadar toplamıdır (kısıtlı ortalama)."""
    n = Y.shape[0]
    yy = np.minimum(Y, kmax).astype(np.int64)
    unc = M & ~C; cen = M & C & (Y >= 1)
    U = np.zeros((n, kmax + 2)); Cc = np.zeros((n, kmax + 2))
    ii, tt = np.where(unc); np.add.at(U, (ii, yy[ii, tt]), 1)
    ii, tt = np.where(cen); np.add.at(Cc, (ii, yy[ii, tt]), 1)
    # risk kümesi R(k) = sansürsüz D >= k + sansürlü y >= k + 1
    Ru = np.cumsum(U[:, ::-1], 1)[:, ::-1]
    Rc = np.cumsum(Cc[:, ::-1], 1)[:, ::-1]
    R = Ru + np.c_[Rc[:, 1:], np.zeros(n)]
    with np.errstate(all='ignore'):
        h = np.where(R > 0, U / np.maximum(R, 1e-12), 0.0)
    S = np.cumprod(1 - h, 1)                 # S(k) = P(D > k)
    gozlem = (U + Cc) > 0
    enb = np.where(gozlem.any(1), kmax + 1 - np.argmax(gozlem[:, ::-1], 1), 0)
    k = np.arange(kmax + 2)[None, :]
    mean = (S * (k < enb[:, None])).sum(1)
    yok = unc.sum(1) == 0
    return np.where(yok, m0(Y, C, M), mean)


def m6_ses(Y, C, M, alfa):
    """Sansürlü üstel düzeltme: bilinen her günde düzey l, sansürsüz günde satışla, sansürlü günde Poisson(l) altında
    E[D | D >= y] ile güncellenir: l <- l + alfa (x - l). Başlangıç düzeyi ilk 28 günün M1 düzeyidir.
    Dönüş: son düzey ve bir adım öncesi sansürlü günlük log olabilirlik toplamı."""
    n, t = Y.shape
    l = np.maximum(m1(Y[:, :28], C[:, :28], M[:, :28]), 1e-3)
    ll = 0.0
    for j in range(t):
        m = M[:, j]
        if not m.any(): continue
        y = Y[:, j]; c = C[:, j] & m
        u = m & ~c
        if j >= 28:
            ll += _logpmf(y[u], np.maximum(l[u], 1e-6)).sum()
            pc = c & (y >= 1)
            ll += _logsf(y[pc], np.maximum(l[pc], 1e-6)).sum()
        x = np.where(c, kosullu_beklenti(y, l), y)
        l = np.where(m, np.maximum(l + alfa * (x - l), 1e-4), l)
    return l, ll


def m6_secim(Y, C, M, adaylar=(0.01, 0.03, 0.1, 0.3)):
    """Düzeltme katsayısı bütün seriler için ortak olarak bir adım öncesi sansürlü olabilirlikle seçilir."""
    best = None
    for a in adaylar:
        l, ll = m6_ses(Y, C, M, a)
        if best is None or ll > best[1]: best = (a, ll, l)
    return best[2], best[0]


# ---------------------------------------------------------------- M4 ailesi: sansürlü Poisson-gama ampirik Bayes
def gruplar(Y, C, M, KEY, cens=True, nk=NK):
    """(seri, anahtar, y, c) dörtlüleri ve sayıları."""
    ii, tt = np.where(M)
    y = Y[ii, tt].astype(np.int64); k = KEY[ii, tt].astype(np.int64)
    c = (C[ii, tt] if cens else np.zeros(len(ii), bool)).astype(np.int64)
    cod = ((ii.astype(np.int64) * nk + k) * 64 + np.minimum(y, 63)) * 2 + c
    u, cnt = np.unique(cod, return_counts=True)
    c_ = u % 2; y_ = (u // 2) % 64; k_ = (u // 128) % nk; i_ = u // (128 * nk)
    return dict(i=i_, k=k_, y=y_.astype(float), c=c_.astype(bool), n=cnt.astype(float))


def tasarim(g, SID, CID, hiyerarsi=True, kovaryat=True, hafta=0):
    """Doğrusal yordayıcı için sütun indeksleri: sabit, mağaza, alt kategori, gün, fiyat durumu, ürün yaşı ve
    (dinamik sürümde) eğitim penceresinin haftası."""
    k = g['k'] % NK; w = g['k'] // NK
    cols = [np.zeros(len(g['i']), np.int64)]; off = 1
    if hiyerarsi:
        cols.append(off + SID[g['i']]); off += SID.max() + 1
        cols.append(off + CID[g['i']]); off += CID.max() + 1
    if kovaryat:
        yas = k // 35; r2 = k % 35
        cols.append(off + r2 // 5); off += 7
        cols.append(off + r2 % 5); off += 5
        cols.append(off + yas); off += 6
    if hafta:
        cols.append(off + w); off += hafta
    return np.stack(cols, 1), off


def referans(SID, CID, hiyerarsi=True, kovaryat=True, hafta=0):
    """Her etken bloğunun ilk düzeyinin katsayı indeksi. Bu katsayılar sıfıra sabitlenir (referans kodlama), böylece
    sabit terim ile blok etkileri arasındaki tam eşdoğrusallık ortadan kalkar."""
    out = []; off = 1
    if hiyerarsi:
        out.append(off); off += SID.max() + 1
        out.append(off); off += CID.max() + 1
    if kovaryat:
        for k in (7, 5, 6): out.append(off); off += k
    if hafta: out.append(off)
    return out


def _mix_terimleri(y, mu, c, a, b):
    """Etiket hatası payları a = P(gerçekte sansürsüz | bayraklı), b = P(gerçekte sansürlü | bayraksız) altında gün
    olabilirliği ve mu'ya göre türevi."""
    lp0 = _logpmf(y, mu); p0 = np.exp(lp0)
    p1 = np.where(y >= 1, np.clip(gammainc(np.maximum(y, 1e-12), mu), 1e-300, 1), 1.0)
    d0 = p0 * (y / np.maximum(mu, 1e-300) - 1)
    d1 = np.where(y >= 1, np.exp(_logpmf(np.maximum(y - 1, 0), mu)), 0.0)
    w1 = np.where(c, 1 - a, b)            # gerçekte sansürlü olma ağırlığı
    L = w1 * p1 + (1 - w1) * p0
    dL = w1 * d1 + (1 - w1) * d0
    return np.maximum(L, 1e-300), dL


def glm_fit(g, X, p, ofs, ridge=1e-3, beta0=None, a=0.0, b=0.0, zw=None):
    """Ortak katsayılar. a = b = 0 iken kesin etiketli sansürlü Poisson olabilirliği, aksi hâlde etiket hatası karışım
    olabilirliği. zw verilirse sansürsüz sıfır günlerinin Poisson bileşenine düşen ağırlığıdır (sıfır şişkin sürüm)."""
    y, c, n = g['y'], g['c'], g['n']
    nn = n if zw is None else n * zw
    karisim = (a > 0) or (b > 0)
    cen = c & (y >= 1); unc = ~c

    def f(bb):
        eta = bb[X].sum(1) + ofs; mu = np.exp(eta)
        ll = np.zeros_like(mu); gr = np.zeros_like(mu)
        if karisim:
            L, dL = _mix_terimleri(y, mu, c, a, b)
            ll = nn * np.log(L); gr = nn * dL / L * mu
        else:
            ll[unc] = nn[unc] * (y[unc] * eta[unc] - mu[unc])
            gr[unc] = nn[unc] * (y[unc] - mu[unc])
            if cen.any():
                sf = np.clip(gammainc(y[cen], mu[cen]), 1e-300, 1)
                ll[cen] = nn[cen] * np.log(sf)
                pm = np.exp(_logpmf(y[cen] - 1, mu[cen]))
                gr[cen] = nn[cen] * mu[cen] * pm / sf
        G = np.zeros(p)
        for j in range(X.shape[1]): G += np.bincount(X[:, j], weights=gr, minlength=p)
        pen = ridge * (bb[1:] ** 2).sum()
        G[1:] -= 2 * ridge * bb[1:]
        return -(ll.sum() - pen), -G
    b0 = np.zeros(p) if beta0 is None else beta0
    if beta0 is None: b0[0] = np.log(max((y * n).sum() / n.sum(), 1e-6))
    r = minimize(f, b0, jac=True, method='L-BFGS-B', options=dict(maxiter=1000))
    return r.x


def seri_olabilirlik(g, mu, nser, a=0.0, b=0.0, pz=None, zgrup=None):
    """Her seri için çarpan ızgarası üzerinde log olabilirlik (nser x |UG|).
    a, b > 0: etiket hatası karışımı. pz: sıfır şişkinlik olasılığı (grup başına), zgrup: grup indeksleri."""
    L = np.zeros((nser, len(UG)))
    y, c, n, i = g['y'], g['c'], g['n'], g['i']
    if a == 0.0 and b == 0.0 and pz is None:
        unc = ~c
        su = np.bincount(i[unc], weights=n[unc] * y[unc], minlength=nser)
        sm = np.bincount(i[unc], weights=n[unc] * mu[unc], minlength=nser)
        L += su[:, None] * np.log(UG)[None, :] - sm[:, None] * UG[None, :]
        cen = np.where(c & (y >= 1))[0]
        for ch in np.array_split(cen, max(1, len(cen) // 20000 + 1)):
            if len(ch) == 0: continue
            np.add.at(L, i[ch], n[ch][:, None] * _logsf(y[ch][:, None], UG[None, :] * mu[ch][:, None]))
        return L
    if pz is not None:
        # sıfır şişkin: sansürsüz y = 0 -> log(pz + (1 - pz) e^{-u mu}), sansürsüz y > 0 -> log(1 - pz) + Poisson,
        # sansürlü y >= 1 -> log(1 - pz) + log P(D >= y), sansürlü y = 0 -> 0
        pzg = pz[zgrup]
        unc = ~c & (y > 0)
        su = np.bincount(i[unc], weights=n[unc] * y[unc], minlength=nser)
        sm = np.bincount(i[unc], weights=n[unc] * mu[unc], minlength=nser)
        L += su[:, None] * np.log(UG)[None, :] - sm[:, None] * UG[None, :]
        cen = np.where(c & (y >= 1))[0]
        for ch in np.array_split(cen, max(1, len(cen) // 20000 + 1)):
            if len(ch) == 0: continue
            np.add.at(L, i[ch], n[ch][:, None] * _logsf(y[ch][:, None], UG[None, :] * mu[ch][:, None]))
        z0 = np.where(~c & (y == 0))[0]
        for ch in np.array_split(z0, max(1, len(z0) // 20000 + 1)):
            if len(ch) == 0: continue
            q = pzg[ch][:, None]
            np.add.at(L, i[ch], n[ch][:, None] * np.log(q + (1 - q) * np.exp(-UG[None, :] * mu[ch][:, None])))
        return L
    allg = np.arange(len(y))
    for ch in np.array_split(allg, max(1, len(allg) // 20000 + 1)):
        m = UG[None, :] * mu[ch][:, None]; yy = y[ch][:, None]
        lp = _logpmf(yy, m)
        ls = np.where(yy >= 1, _logsf(np.maximum(yy, 1), m), 0.0)
        w1 = np.where(c[ch], 1 - a, b)[:, None]
        v = np.logaddexp(np.log(np.maximum(w1, 1e-300)) + ls, np.log(np.maximum(1 - w1, 1e-300)) + lp)
        np.add.at(L, i[ch], n[ch][:, None] * v)
    return L


def onsel_log(phi):
    """Ortalaması 1, varyansı phi olan gama önselinin ızgara hücrelerine düşen log olasılıkları."""
    a = 1.0 / phi
    cdf = gamma_dist.cdf(_SINIR, a, scale=1.0 / a)
    return np.log(np.maximum(np.diff(cdf), 1e-300))


def secim_log(g, mu, nser, pz=None, zgrup=None):
    """Seçim olasılığının log değeri (nser x |UG|): eğitim penceresinde en az bir birim satış gözlenmesi.
    Sansürlü ve satışsız günler satış üretemediği için dışarıda kalır. Sıfır şişkin sürümde her gün satışsız kalma
    olasılığı pz + (1 - pz) e^{-u mu} olur."""
    y, c, n, i = g['y'], g['c'], g['n'], g['i']
    etkin = ~(c & (y == 0))
    if pz is None:
        Sm = np.bincount(i[etkin], weights=n[etkin] * mu[etkin], minlength=nser)
        l0 = -Sm[:, None] * UG[None, :]
    else:
        l0 = np.zeros((nser, len(UG)))
        ix = np.where(etkin)[0]; q = pz[zgrup]
        for ch in np.array_split(ix, max(1, len(ix) // 20000 + 1)):
            if len(ch) == 0: continue
            qq = q[ch][:, None]
            np.add.at(l0, i[ch], n[ch][:, None] * np.log(qq + (1 - qq) * np.exp(-UG[None, :] * mu[ch][:, None])))
    return np.log(np.maximum(-np.expm1(l0), 1e-300))


def eb(L, Ls=None):
    """Gama önseli (ortalama 1, varyans phi) ile ampirik Bayes. phi, marjinal olabilirliği log phi üzerinde sürekli
    arama ile en büyükler. Ls verilirse marjinal olabilirlik seçim koşulludur: seriler eğitimde en az bir satış
    gözlendiği için analize girer, bu nedenle her serinin marjinal olasılığı seçim olasılığına bölünür. Seçim
    olasılığı u'ya bağlı olsa da verilen phi için u'nun sonsalı bu düzeltmeden etkilenmez."""
    def mlv(lphi):
        lp = onsel_log(np.exp(lphi))[None, :]
        v = logsumexp(L + lp, axis=1)
        if Ls is not None: v = v - logsumexp(Ls + lp, axis=1)
        return v
    r = minimize_scalar(lambda x: -mlv(x).sum(), bounds=np.log(PHI_ARALIK), method='bounded', options=dict(xatol=1e-3))
    phi = float(np.exp(r.x)); lp = L + onsel_log(phi)[None, :]
    W = np.exp(lp - logsumexp(lp, axis=1)[:, None])
    return W, phi, float(mlv(r.x).sum())


def _parcalar(n, boy=20000):
    return [np.arange(k, min(k + boy, n)) for k in range(0, n, boy)]


def _segment_topla(V, ii, nser):
    """V (k x G) satırlarını seri indeksine (ii, artan sıralı) göre toplar."""
    out = np.zeros((nser, V.shape[1]))
    bas = np.r_[0, np.where(np.diff(ii) != 0)[0] + 1]
    out[ii[bas]] += np.add.reduceat(V, bas, axis=0)
    return out


class Model4:
    """Seçim koşullu marjinal olabilirliğin ortak katsayılar (beta), dağılım parametresi (log phi) ve isteğe bağlı sıfır
    şişkinlik olasılıkları üzerinde doğrudan en büyüklenmesi. Seri çarpanı u, 501 noktalı ızgarada tümlev dışı
    bırakılır. Gradyan, Fisher özdeşliğiyle (log marjinal olabilirliğin türevi = tam veri türevinin sonsal beklentisi)
    hesaplanır. log phi'ye göre türev merkezi farkla alınır."""

    def __init__(self, g, X, p, nser, a=0.0, b=0.0, zgrup=None, nz=0, secim=True, ridge=1e-3, sabit=()):
        self.g, self.X, self.p, self.nser = g, X, p, nser
        self.sabit = list(sabit)
        self.a, self.b, self.secim, self.ridge = a, b, secim, ridge
        y, c = g['y'], g['c']
        self.zgrup = zgrup; self.nz = nz; zi = zgrup is not None
        w1 = np.where(c, 1.0 - a, b)                            # gerçekte sansürlü olma ağırlığı
        self.w1 = w1
        bos = (w1 >= 1.0) & (y == 0)                             # kesin bayraklı satışsız gün: bilgi taşımaz
        kapali = (w1 <= 0.0) & ~(zi & (y == 0))                  # saf Poisson günü: kapalı biçim
        self.kapali = np.where(kapali)[0]
        self.izgara = np.where(~kapali & ~bos)[0]
        self.etkin = np.where(~(c & (y == 0)))[0]                # seçim olasılığına giren günler
        self.lgy = gammaln(y + 1)

    # ---- yardımcılar
    def _gun(self, j, mu, q):
        """Izgara günleri için değer ve eta'ya göre türev (k x G), sıfır şişkinlikte q'ya göre türev."""
        g = self.g; y = g['y'][j][:, None]; m = UG[None, :] * mu[j][:, None]
        w1 = self.w1[j][:, None]
        logm = np.log(np.maximum(m, 1e-300))
        lP = y * logm - m - self.lgy[j][:, None]
        dq = None
        if self.zgrup is not None:
            qq = q[self.zgrup[j]][:, None]
            sifir = (y == 0)
            # sansürsüz sıfır: log(q + (1-q) e^{-m}); sansürsüz pozitif: log(1-q) + Poisson; sansürlü pozitif: log(1-q) + log S
            z = qq + (1 - qq) * np.exp(-m)
            lS = np.where(y >= 1, np.log(np.clip(gammainc(np.maximum(y, 1e-12), m), 1e-300, 1)), 0.0)
            ldS = np.where(y >= 1, logm + (y - 1) * logm - m - gammaln(np.maximum(y, 1)) - lS, -np.inf)
            sans = (w1 >= 1.0)
            v = np.where(sifir & ~sans, np.log(z), np.log(1 - qq) + np.where(sans, lS, lP))
            d = np.where(sifir & ~sans, -(1 - qq) * m * np.exp(-m) / z, np.where(sans, np.exp(ldS), y - m))
            dq = np.where(sifir & ~sans, (1 - np.exp(-m)) / z, -1.0 / (1 - qq))
            return v, d, dq
        lS = np.where(y >= 1, np.log(np.clip(gammainc(np.maximum(y, 1e-12), m), 1e-300, 1)), 0.0)
        ldS = np.where(y >= 1, logm + (y - 1) * logm - m - gammaln(np.maximum(y, 1)), -np.inf)   # log dS/deta
        la = np.log(np.maximum(w1, 1e-300)) + lS; lb = np.log(np.maximum(1 - w1, 1e-300)) + lP
        v = np.logaddexp(la, lb)
        d = np.where(w1 > 0, w1 * np.exp(ldS - v), 0.0) + (1 - w1) * np.exp(lP - v) * (y - m)
        return v, d, dq

    def _L(self, mu, q):
        g = self.g; i, y, n = g['i'], g['y'], g['n']; nser = self.nser
        k = self.kapali
        su = np.bincount(i[k], weights=n[k] * y[k], minlength=nser)
        sm = np.bincount(i[k], weights=n[k] * mu[k], minlength=nser)
        sb = np.bincount(i[k], weights=n[k] * (y[k] * np.log(np.maximum(mu[k], 1e-300)) - self.lgy[k]), minlength=nser)
        L = su[:, None] * np.log(UG)[None, :] - sm[:, None] * UG[None, :] + sb[:, None]
        if self.zgrup is not None:
            l1q = np.log(1 - q[self.zgrup[k]])
            L += np.bincount(i[k], weights=n[k] * l1q, minlength=nser)[:, None]
        self._onbellek = []
        for ch in _parcalar(len(self.izgara)):
            j = self.izgara[ch]; v, d, dq = self._gun(j, mu, q)
            L += _segment_topla(n[j][:, None] * v, i[j], nser)
            self._onbellek.append((j, d.astype(np.float32), None if dq is None else dq.astype(np.float32)))
        return L

    def _Ls(self, mu, q):
        if not self.secim: return None
        g = self.g; i, n = g['i'], g['n']; e = self.etkin
        if self.zgrup is None:
            Sm = np.bincount(i[e], weights=n[e] * mu[e], minlength=self.nser)
            l0 = -Sm[:, None] * UG[None, :]
        else:
            l0 = np.zeros((self.nser, len(UG)))
            for ch in _parcalar(len(e)):
                j = e[ch]; qq = q[self.zgrup[j]][:, None]
                l0 += _segment_topla(n[j][:, None] * np.log(qq + (1 - qq) * np.exp(-UG[None, :] * mu[j][:, None])), i[j], self.nser)
        self._l0 = l0
        return np.log(np.maximum(-np.expm1(l0), 1e-300))

    def _ml(self, L, Ls, lphi):
        lp = onsel_log(np.exp(lphi))[None, :]
        A = logsumexp(L + lp, axis=1)
        if Ls is None: return A.sum(), A, None
        Bv = logsumexp(Ls + lp, axis=1)
        return (A - Bv).sum(), A, Bv

    def ayir(self, th):
        p = self.p; beta = th[:p]; lphi = th[p]
        q = None if self.zgrup is None else 1 / (1 + np.exp(-th[p + 1:]))
        return beta, lphi, q

    def f(self, th):
        g = self.g; i, y, n = g['i'], g['y'], g['n']; X = self.X; p = self.p
        beta, lphi, q = self.ayir(th)
        mu = np.exp(np.clip(beta[X].sum(1), -30, 15))
        L = self._L(mu, q); Ls = self._Ls(mu, q)
        ml, A, Bv = self._ml(L, Ls, lphi)
        lp = onsel_log(np.exp(lphi))[None, :]
        Wp = np.exp(L + lp - A[:, None])
        eu = Wp @ UG
        gr = np.zeros(len(y)); gq = np.zeros(self.nz)
        k = self.kapali
        gr[k] = n[k] * (y[k] - eu[i[k]] * mu[k])
        if self.zgrup is not None:
            gq -= np.bincount(self.zgrup[k], weights=n[k] / (1 - q[self.zgrup[k]]), minlength=self.nz)
        for j, d, dq in self._onbellek:
            Wj = Wp[i[j]]
            gr[j] = n[j] * (Wj * d).sum(1)
            if dq is not None:
                gq += np.bincount(self.zgrup[j], weights=n[j] * (Wj * dq).sum(1), minlength=self.nz)
        if Ls is not None:
            Q = np.exp(Ls + lp - Bv[:, None])                      # seçim koşullu önsel
            e = self.etkin
            if self.zgrup is None:
                # d/deta log P(sel | u) = u mu e^{-uS} / (1 - e^{-uS}) = u mu / expm1(uS)
                Sm = -self._l0[:, 1] / UG[1]
                h = (Q * (UG[None, :] / np.maximum(np.expm1(UG[None, :] * Sm[:, None]), 1e-300))).sum(1)
                gr[e] -= n[e] * mu[e] * h[i[e]]
            else:
                P0 = np.exp(self._l0); r = P0 / np.maximum(1 - P0, 1e-300)   # Π z / (1 - Π z)
                for ch in _parcalar(len(e)):
                    j = e[ch]; qq = q[self.zgrup[j]][:, None]; m = UG[None, :] * mu[j][:, None]
                    z = qq + (1 - qq) * np.exp(-m)
                    Rj = Q[i[j]] * r[i[j]]
                    gr[j] -= n[j] * (Rj * ((1 - qq) * m * np.exp(-m) / z)).sum(1)
                    gq -= np.bincount(self.zgrup[j], weights=n[j] * (-(Rj * ((1 - np.exp(-m)) / z)).sum(1)), minlength=self.nz)
        G = np.zeros(p)
        for c_ in range(X.shape[1]): G += np.bincount(X[:, c_], weights=gr, minlength=p)
        G[1:] -= 2 * self.ridge * beta[1:]
        # log phi türevi: önsel hücre olasılıklarının türevi sayısal (501 noktalı vektör), veri kısmı sonsal ağırlıklarla kesin
        h = 1e-4
        dlp = (onsel_log(np.exp(lphi + h)) - onsel_log(np.exp(lphi - h))) / (2 * h)
        gphi = float((Wp @ dlp).sum())
        if Ls is not None: gphi -= float((Q @ dlp).sum())
        out = ml - self.ridge * (beta[1:] ** 2).sum()
        grad = np.r_[G, gphi]
        if self.zgrup is not None: grad = np.r_[grad, gq * q * (1 - q)]
        self.son = dict(W=Wp, ml=ml, phi=float(np.exp(lphi)), q=q, beta=beta)
        return -out, -grad

    def coz(self, th0, maxiter=200):
        lo = [None] * self.p + [np.log(PHI_ARALIK[0])] + [-12.0] * self.nz
        hi = [None] * self.p + [np.log(PHI_ARALIK[1])] + [6.0] * self.nz
        th0 = np.array(th0, float).copy()
        for j in self.sabit: lo[j] = hi[j] = 0.0; th0[j] = 0.0
        r = minimize(self.f, th0, jac=True, method='L-BFGS-B', bounds=list(zip(lo, hi)),
                     options=dict(maxiter=maxiter, ftol=1e-10, gtol=1e-5))
        self.f(r.x)
        return r


def _baslangic(g, p, nz, X=None, ridge=1e-3, sabit=()):
    """Başlangıç değerleri. X verilirse ortak katsayılar, sansürsüz günlerde seri çarpanı olmadan kurulan Poisson
    regresyonundan alınır (kapalı biçimli, ızgarasız ve hızlı bir ön çözüm)."""
    th = np.zeros(p + 1 + nz)
    th[0] = np.log(max((g['y'] * g['n']).sum() / g['n'].sum(), 1e-6)); th[p] = np.log(0.5)
    if nz: th[p + 1:] = np.log(0.05 / 0.95)
    if X is not None:
        u = ~g['c']; Xu = X[u]; y = g['y'][u]; n = g['n'][u]
        def f(b):
            eta = np.clip(b[Xu].sum(1), -30, 15); mu = np.exp(eta)
            r = n * (y - mu); G = np.zeros(p)
            for c_ in range(Xu.shape[1]): G += np.bincount(Xu[:, c_], weights=r, minlength=p)
            G[1:] -= 2 * ridge * b[1:]
            return -((n * (y * eta - mu)).sum() - ridge * (b[1:] ** 2).sum()), -G
        bd = [(None, None)] * p
        for j in sabit: bd[j] = (0.0, 0.0)
        rr = minimize(f, th[:p], jac=True, method='L-BFGS-B', bounds=bd, options=dict(maxiter=300))
        th[:p] = rr.x
    return th


def m4(Y, C, M, KEY, SID, CID, hiyerarsi=True, kovaryat=True, cens=True, etiket=None, sifir_sisme=False,
       hafta=None, secim=True, maxiter=200, bas=None):
    """M4 ailesi. Ortak katsayılar, phi ve (varsa) sıfır şişkinlik olasılıkları seçim koşullu marjinal olabilirliğin
    doğrudan en büyüklenmesiyle birlikte tahmin edilir.
    etiket: None (kesin etiket), (a, b) çifti ya da 'tahmin'. 'tahmin' durumunda a ve b, kesin etiketli M4 çözümünden
    başlayan ve yalnız phi'yi yeniden en büyükleyen tarama ile seçilir, seçilen çift için tam çözüm yapılır.
    sifir_sisme: bölüm indeksleri verilirse bölüm başına sıfır şişkinlik olasılığı tahmin edilir.
    hafta: eğitim penceresindeki gün başına hafta indeksi matrisi (dinamik düzeyli sürüm).
    secim: True iken marjinal olabilirlik, serinin eğitimde en az bir satışla seçilmesine koşulludur."""
    nser = Y.shape[0]
    nh = 0 if hafta is None else int(hafta[M].max()) + 1
    KEYe = KEY if hafta is None else KEY + NK * hafta
    g = gruplar(Y, C, M, KEYe, cens, nk=NK * max(nh, 1))
    X, p = tasarim(g, SID, CID, hiyerarsi, kovaryat, hafta=nh)
    sb = referans(SID, CID, hiyerarsi, kovaryat, hafta=nh)
    zgrup = None; nz = 0
    if sifir_sisme is not False:
        zgrup = sifir_sisme[g['i']]; nz = int(sifir_sisme.max()) + 1
    tarama = None
    def _ilk(nz_):
        """Başlangıç: bas (beta, log phi) verilirse o çözümden, aksi hâlde Poisson regresyonu ön çözümünden."""
        if bas is None: return _baslangic(g, p, nz_, X, sabit=sb)
        th = _baslangic(g, p, nz_); bb, lph = bas
        th[:len(bb)] = bb; th[p] = lph
        return th
    if etiket == 'tahmin':
        m0 = Model4(g, X, p, nser, secim=secim, sabit=sb); r0 = m0.coz(_ilk(0), maxiter)
        th0 = r0.x.copy(); beta0 = th0[:p]; mu0 = np.exp(beta0[X].sum(1))
        tarama = {}
        for a in (0.0, 0.05, 0.1, 0.2, 0.35, 0.5):
            for b in (0.0,):     # b > 0 bütün bayraksız günleri ızgara hesabına taşıdığı için b sıfıra sabitlenmiştir
                mm = Model4(g, X, p, nser, a=a, b=b, secim=secim, sabit=sb)
                L = mm._L(mu0, None); Ls = mm._Ls(mu0, None)
                rr = minimize_scalar(lambda x: -mm._ml(L, Ls, x)[0], bounds=np.log(PHI_ARALIK), method='bounded')
                tarama[(a, b)] = -rr.fun
        a, b = max(tarama, key=tarama.get)
        if (a, b) == (0.0, 0.0):
            mod, r = m0, r0
        else:
            mod = Model4(g, X, p, nser, a=a, b=b, secim=secim, sabit=sb); r = mod.coz(th0, maxiter)
    else:
        a, b = (0.0, 0.0) if etiket is None else tuple(etiket)
        mod = Model4(g, X, p, nser, a=a, b=b, zgrup=zgrup, nz=nz, secim=secim, sabit=sb)
        r = mod.coz(_ilk(nz), maxiter)
    s = mod.son
    fit = dict(W=s['W'], beta=s['beta'], phi=s['phi'], ml=float(s['ml']), em_tur=int(r.nit), basari=bool(r.success),
               a=a, b=b, pz=s['q'], hiy=hiyerarsi, kov=kovaryat, nh=nh)
    if tarama is not None: fit['tarama'] = {f'{k[0]}_{k[1]}': v for k, v in tarama.items()}
    return fit


def a_profili(Y, C, M, KEY, SID, CID, fit, adaylar=(0.0, 0.05, 0.1, 0.2, 0.35, 0.5)):
    """Etiket hatası payı a için profil log olabilirlik: ortak katsayılar M4 çözümünde tutulur, phi her a için yeniden
    en büyüklenir. Bayraklı günün katkısı (1 - a) P(D >= y) + a P(D = y) olduğu ve P(D >= y) >= P(D = y) olduğu için
    olabilirlik her gün için a'da azalandır, a sansürlü satış verisinden tek başına tanımlanamaz."""
    g = gruplar(Y, C, M, KEY, True); X, p = tasarim(g, SID, CID, fit['hiy'], fit['kov'])
    mu = np.exp(np.clip(fit['beta'][X].sum(1), -30, 15)); out = {}
    for a in adaylar:
        mm = Model4(g, X, p, Y.shape[0], a=a)
        L = mm._L(mu, None); Ls = mm._Ls(mu, None)
        rr = minimize_scalar(lambda x: -mm._ml(L, Ls, x)[0], bounds=np.log(PHI_ARALIK), method='bounded')
        out[a] = float(-rr.fun)
    return out


def m4_mu(fit, KEYm, Mm, SID, CID, hafta=None, son_hafta=4):
    """Günlük ortak değişken ortalaması (n x t), u = 1 düzeyinde. Dinamik sürümde test günleri için eğitim penceresinin
    son son_hafta haftasının ortalama hafta etkisi kullanılır."""
    b = fit['beta']; n, t = KEYm.shape
    eta = np.full((n, t), b[0]); off = 1
    if fit['hiy']:
        ns = SID.max() + 1; nc = CID.max() + 1
        eta += b[off + SID][:, None]; off += ns
        eta += b[off + CID][:, None]; off += nc
    if fit['kov']:
        yas = KEYm // 35; r2 = KEYm % 35
        eta += b[off + r2 // 5]; off += 7
        eta += b[off + r2 % 5]; off += 5
        eta += b[off + yas]; off += 6
    if fit['nh']:
        hb = b[off:off + fit['nh']]
        if hafta is None:
            eta += hb[-son_hafta:].mean()
        else:
            eta += hb[np.clip(hafta, 0, fit['nh'] - 1)]
    return np.exp(eta) * Mm


# ---------------------------------------------------------------- dağılım yardımcıları
def karisim_pmf(W, tot, K):
    """Toplam talep için Poisson karışımı olasılıkları (n x K+1). W: (n x g) ağırlıklar, tot: (n,) u = 1'deki toplam."""
    ks = np.arange(K + 1)
    out = np.zeros((len(tot), K + 1))
    for ch in np.array_split(np.arange(len(tot)), max(1, len(tot) // 400)):
        m = UG[None, :, None] * tot[ch][:, None, None]
        lp = ks[None, None, :] * np.log(np.maximum(m, 1e-300)) - m - gammaln(ks + 1)[None, None, :]
        out[ch] = np.einsum('ng,ngk->nk', W[ch], np.exp(lp))
    return out


def poisson_pmf(lam_tot, K):
    ks = np.arange(K + 1)
    m = np.maximum(lam_tot, 1e-12)[:, None]
    return np.exp(ks[None, :] * np.log(m) - m - gammaln(ks + 1)[None, :])
