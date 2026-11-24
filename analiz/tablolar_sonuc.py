# -*- coding: utf-8 -*-
"""Analiz sonucuna bağlı ana metin ve ek tabloları. Bütün değerler cikti/sonuclar.json dosyasından okunur."""
from sayilar import *

AD = {'M0': 'Satışı talep sayan', 'M1': 'Silme', 'M2': 'Kayan profil ataması', 'M3': 'Seri içi sansürlü Poisson',
      'M5': 'Kaplan-Meier', 'M6': 'Sansürlü üstel düzeltme', 'M4': 'Havuzlu sansürlü',
      'M4R': 'M4, denetimli etiket hatası', 'M4Z': 'M4, sıfır şişkin', 'M4D': 'M4, haftalık düzey', 'M4S': 'M4, sansürü yok sayan',
      'M4H': 'M4, hiyerarşisiz', 'M4K': 'M4, hiyerarşisiz ve ortak değişkensiz', 'TB': 'Tam bilgili eğitim kıyası',
      'TK': 'Test kâhini'}
SIRA = ['M0', 'M1', 'M2', 'M3', 'M5', 'M6', 'M4', 'M4R', 'M4Z', 'M4D', 'M4S', 'M4H', 'M4K', 'TB', 'TK']
TIRE = '–'

def g(*yol):
    x = R
    for k in yol:
        if x is None: return None
        if isinstance(x, dict): x = x.get(str(k)) if str(k) in x else x.get(k)
        elif isinstance(x, list) and isinstance(k, int) and k < len(x): x = x[k]
        else: return None
    return x

def Y(x, d=1, isaret=False): return TIRE if x is None else yz(x, d, isaret)
def F(x, d=3): return TIRE if x is None else f(x, d)
def ARALIK(c, d=1, yuzde=True):
    if c is None: return TIRE
    fm = (lambda v: yz(v, d)) if yuzde else (lambda v: f(v, d))
    return f'{fm(c["deger"])} ({fm(c["alt"])} – {fm(c["ust"])})'
def YILDIZ(x):
    if x is None: return TIRE
    s = f(x['fark'], 3)
    return s + ('*' if x.get('p_holm', 1) < 0.05 else '')
def modeller(sozluk): return [m for m in SIRA if sozluk and m in sozluk]
KAT_TARIH = {0: '01.01', 1: '29.01', 2: '26.02', 3: '26.03'}   # 2026

# ------------------------------------------------------------------ ana metin
def t_ana_olcut():
    O = g('S_orta', 'olcut'); C = g('S_orta', 'ci')
    sat = []
    for m in [m for m in modeller(O) if m != 'M4R']:
        o = O[m]; c = (C or {}).get(m, {})
        geri = m != 'TK'
        sat.append([f'{m} {AD[m]}',
                    Y(o['gk_yanlilik'], 1) if geri else TIRE,
                    Y(o['gk_wape'], 1) if geri else TIRE,
                    F(o['kiyas_sapma'], 3) if m != 'TB' else TIRE,
                    F(o['crps'], 3), Y(o['kapsama80'], 1), F(o['maliyet90'], 2)])
    return ('Orta sansür şiddetinde geri kazanım, tahmin ve maliyet ölçütleri',
            ['Model', 'GY', 'GAMH', 'KS', 'SSOS', '%80 aralık kapsaması', 'Maliyet (k = 0,90)'], sat,
            f'Dört başlangıç noktasında {n(g("S_orta", "n_gozlem"))} seri-başlangıç gözlemi, {n(g("S_orta", "n_seri"))} seri ve '
            f'{n(g("S_orta", "n_magaza"))} mağaza. GY ve GAMH eğitim penceresinde, KS, SSOS, kapsama ve maliyet test penceresinde hesaplanmıştır. '
            'TK test penceresinin gerçek talebiyle kurulduğu için geri kazanım ölçütleri TK için tanımlı tutulmamıştır. '
            'Maliyet talep birimi başına verilmiştir, hiç stok tutmayan politikanın maliyeti 9,00 birimdir. '
            'M4 için %95 önyükleme aralıkları ve bütün karşılaştırmalar {T:karsilastirma} içinde verilmiştir.')

def t_karsilastirma():
    K = g('S_orta', 'karsilastirma') or {}
    olc = [('gk_yanlilik_mutlak', '|GY|'), ('gk_wape', 'GAMH'), ('gk_wape_medyan', 'GAMH (medyan)'), ('kiyas_sapma', 'KS'),
           ('crps', 'SSOS'), ('maliyet90', 'Maliyet (k = 0,90)')]
    rak = [m for m in modeller(K.get('gk_wape')) if m != 'M4R']
    sat = []
    C = g('S_orta', 'ci', 'M4') or {}
    sat.append(['M4 düzeyi (%95 aralık)', ARALIK(C.get('gk_yanlilik'), 1), ARALIK(C.get('gk_wape'), 1), ARALIK(C.get('gk_wape_medyan'), 1),
                ARALIK(C.get('kiyas_sapma'), 3, False), ARALIK(C.get('crps'), 3, False), ARALIK(C.get('maliyet90'), 2, False)])
    for m in rak:
        sat.append([f'M4 − {m}'] + [YILDIZ(K.get(o, {}).get(m)) for o, _ in olc])
    return ('M4 modelinin kıyas modelleriyle eşleştirilmiş karşılaştırması (orta sansür şiddeti)',
            ['Karşılaştırma', 'GY', 'GAMH', 'GAMH (medyan)', 'KS', 'SSOS', 'Maliyet (k = 0,90)'], sat,
            'İlk satır M4 modelinin düzeyini ve iki aşamalı hiyerarşik önyüklemeden (B = 1 000) alınan %95 aralığını vermektedir. '
            'Diğer satırlar M4 ile kıyas modeli arasındaki eşleştirilmiş farktır, GY sütununda fark mutlak yanlılık üzerinden alınmıştır ve negatif fark M4 lehinedir. '
            'Farklar yuvarlanmamış değerlerden hesaplanmıştır. * Her ölçüt ailesinde Holm düzeltmeli p < 0,05. Farkların güven aralıkları ve düzeltilmiş olasılık değerleri {EK:karsilastirma_tam} içindedir.')

def t_heterojenlik():
    H = g('S_orta', 'heterojenlik')
    ad = {'sabit': 'Sabit', 'log_OTA': 'log(ortalama talep aralığı)', 'DK2': 'Talep büyüklüğünün DK²',
          'bayrak_orani': 'Sansürlü gün oranı', 'log1p_gozlenen_satis': 'log(1 + gözlenen satış)'}
    sat = []
    if H:
        for a, k, s, pv in zip(H['ad'], H['katsayi'], H['se'], H['p']):
            sat.append([ad[a], f(k, 3), f(s, 3), p(pv).replace('p = ', '').replace('p < ', '< ')])
        sat.append(['Gözlem, R²', n(H['n']), f(H['r2'], 3), TIRE])
    return ('Sansür düzeltmesi kazancının seri nitelikleriyle regresyonu',
            ['Açıklayıcı değişken', 'Katsayı', 'Kümelenmiş SH', 'p'], sat,
            'Bağımlı değişken M0 ve M4 modellerinin seri düzeyindeki mutlak geri kazanım hatası farkıdır (birim, pozitif değer M4 lehine). '
            'Açıklayıcı değişkenler başlangıç noktasında gözlenebilen eğitim satışı ve sansür bayrağından hesaplanmıştır. '
            'Standart hatalar mağaza düzeyinde kümelenmiştir (40 küme). DK²: değişkenlik katsayısının karesi.')

def t_gurultu():
    G = g('gurultu') or {}
    ms = ['M1', 'M2', 'M6', 'M4', 'M4R']
    sat = [['Gürültüsüz', Y(g('S_orta', 'sansur_orani'))] + [Y(g('S_orta', 'olcut', m, 'gk_yanlilik'), 1) for m in ms] + [Y(0.0)]]
    for tur, ad in [('FN', 'Yanlış negatif'), ('FP', 'Yanlış pozitif')]:
        for e, r_ in [('05', '0,05'), ('10', '0,10'), ('20', '0,20')]:
            x = G.get(f'{tur}{e}')
            if not x: continue
            ah = [v for v in (x.get('a_hat') or {}).values() if v is not None]
            sat.append([f'{ad}, η = {r_}', Y(x.get('sansur_orani'))] + [Y(g('gurultu', f'{tur}{e}', m, 'gk_yanlilik'), 1) for m in ms]
                       + [Y(sum(ah) / len(ah)) if ah else TIRE])
    fp = G.get('FP20_fark', {}).get('gk_yanlilik')
    ek = ''
    if fp:
        ek = (f' %20 yanlış pozitif hatada M4R ile M4 arasındaki |GY| farkı {f(fp["fark"], 3)} '
              f'(%95 aralık {f(fp["alt"], 3)} – {f(fp["ust"], 3)}, {p(fp["p"])}) olarak bulunmuştur.')
    return ('Stok etiketi gürültüsü altında geri kazanım yanlılığı (GY)',
            ['Senaryo', 'Bayraklı gün oranı'] + ms + ['Denetimden alınan a'], sat,
            'Bütün senaryolar orta sansür şiddetinin gerçek talep dizileri ve gerçek sansür durumları üzerine kurulmuştur. '
            'Denetimden alınan a, eğitim penceresindeki bayraklı günlerin %5’lik rastgele örnekleminde gerçekte sansürsüz çıkan günlerin payıdır ve dört başlangıç noktasının ortalamasıdır.' + ek)

def t_karar():
    O = g('S_orta', 'olcut') or {}
    sat = []
    for m in modeller(O):
        if m in ('TK', 'M4R'): continue
        o = O[m]
        sat.append([m] + [F(o.get(f'maliyet{c}'), 2) for c in (50, 75, 90, 95)] +
                   [F(o.get('pisman_TK90'), 2), F(o.get('pismand_TK90'), 2), F(o.get('pismang_TK90'), 2), Y(o.get('karsilama90'), 1)])
    tk = O.get('TK', {})
    sat.append(['TK'] + [F(tk.get(f'maliyet{c}'), 2) for c in (50, 75, 90, 95)] + ['0,00', '0,00', '0,00', Y(tk.get('karsilama90'), 1)])
    sat.append(['Stoksuz politika', '1,00', '3,00', '9,00', '19,00', TIRE, TIRE, TIRE, '%0,0'])
    return ('Haftalık yenileme politikasında maliyet ve TK modeline göre pişmanlık',
            ['Model', 'Maliyet k = 0,50', 'k = 0,75', 'k = 0,90', 'k = 0,95', 'Pişmanlık k = 0,90', 'Devirli', 'Ölçekli', 'Karşılama k = 0,90'], sat,
            'Maliyetler talep birimi başına verilmiştir (h = 1, p = k/(1 − k)). Pişmanlık modelin maliyeti ile TK maliyeti arasındaki farktır. '
            'Devirli düzende kalan stok sonraki haftaya geçmektedir, ölçekli düzende tahmin mağazanın son 28 günlük satış düzeyine göre ölçeklenmiştir. '
            'Karşılama, karşılanan talebin toplam talebe oranıdır.')

def t_dogal():
    sat = []
    ms = ['M1', 'M2', 'M5', 'M6', 'M4', 'M4D']
    for cr, ad in [('CR1', 'SR1 Geniş'), ('CR2', 'SR2 İhtiyatlı'), ('CR3', 'SR3 Dar'), ('CR4', 'SR4 Negatifsiz geniş'), ('CR5', 'SR5 Dar bayrak, tam küme')]:
        D = g(f'D_{cr}')
        if not D: continue
        sat.append([ad, n(D['n_gozlem']), Y(D['sansur_orani'])] + [Y(g(f'D_{cr}', 'olcut', m, 'kayip_talep_orani', 'deger'), 1) for m in ms])
    c = g('D_CR3', 'olcut', 'M4', 'kayip_talep_orani')
    ek = f' SR3 tanımında M4 için %95 önyükleme aralığı {Y(c["alt"])} – {Y(c["ust"])} olarak hesaplanmıştır.' if c else ''
    return ('Doğal veride tahmin edilen kayıp talep oranı',
            ['Sansür tanımı', 'Seri-başlangıç', 'Bayraklı gün oranı'] + ms, sat,
            'Kayıp talep oranı, eğitim penceresinde tamamlanan talep ile gözlenen satış arasındaki farkın gözlenen satışa oranıdır. '
            'Doğal veride gerçek talep bilinmediği için oranlar doğruluk ölçütü sayılmamakta, tanıma duyarlılığın ölçüsü olarak okunmaktadır.' + ek
            + ' Test penceresindeki satışa uzaklık {EK:dogal_tam} içinde verilmiştir.')

# ------------------------------------------------------------------ ekler
def t_siddet():
    sat = []
    for s, ad in [('S_dusuk', 'Düşük (κ = 0,25)'), ('S_orta', 'Orta (κ = 1)'), ('S_yuksek', 'Yüksek (κ = 2)')]:
        O = g(s, 'olcut') or {}
        for m in modeller(O):
            if m == 'TK': continue
            o = O[m]
            sat.append([ad if m == modeller(O)[0] else '', m, Y(o['gk_yanlilik']), Y(o['gk_wape']), Y(o.get('gk_gun_wape')),
                        F(o['kiyas_sapma']) if m != 'TB' else TIRE, F(o['crps']), F(o['maliyet90'], 2)])
    bilgi = ', '.join(f'{ad} {Y(g(s, "sansur_orani"))}' for s, ad in [('S_dusuk', 'düşük'), ('S_orta', 'orta'), ('S_yuksek', 'yüksek')])
    kayip = ', '.join(f'{ad} {Y(g(s, "kayip_payi"))}' for s, ad in [('S_dusuk', 'düşük'), ('S_orta', 'orta'), ('S_yuksek', 'yüksek')])
    return ('Sansür şiddeti senaryolarında bütün modellerin ölçütleri',
            ['Şiddet', 'Model', 'GY', 'GAMH', 'Gün düzeyi GAMH', 'KS', 'SSOS', 'Maliyet (k = 0,90)'], sat,
            f'Eğitim penceresinde sansürlü gün oranı: {bilgi}. Sansürlü günlerdeki kayıp talebin gerçek eğitim talebine oranı: {kayip}. '
            'Sıfır şişkin ve etiket hatalı sürümler orta şiddette çalıştırılmıştır.')

def t_karsilastirma_tam():
    K = g('S_orta', 'karsilastirma') or {}
    ad = {'gk_yanlilik_mutlak': '|GY|', 'gk_wape': 'GAMH', 'gk_wape_medyan': 'GAMH (medyan)', 'kiyas_sapma': 'KS', 'crps': 'SSOS', 'maliyet90': 'Maliyet (k = 0,90)'}
    sat = []
    for o in ['gk_yanlilik_mutlak', 'gk_wape', 'gk_wape_medyan', 'kiyas_sapma', 'crps', 'maliyet90']:
        for j, m in enumerate(modeller(K.get(o))):
            x = K[o][m]
            sat.append([ad[o] if j == 0 else '', f'M4 − {m}', f(x['fark'], 4), f'{f(x["alt"], 4)} – {f(x["ust"], 4)}',
                        p(x['p']).replace('p = ', '').replace('p < ', '< '), p(x['p_holm']).replace('p = ', '').replace('p < ', '< ')])
    return ('M4 modelinin bütün eşleştirilmiş karşılaştırmaları',
            ['Ölçüt', 'Fark', 'Değer', '%95 aralık', 'p', 'Holm p'], sat,
            'İki aşamalı hiyerarşik önyükleme (önce mağaza, sonra mağaza içindeki seri), B = 1 000. Bütün modellere her tekrarda aynı ağırlıklar uygulanmıştır. '
            'Olasılık değeri 2(k + 1)/(B + 1) ile hesaplandığı için ulaşılabilecek en küçük değer 0,002’dir.')

def t_kat():
    sat = []
    KO = g('S_orta', 'kat_olcut') or {}
    for k in sorted(KO, key=int):
        for j, m in enumerate(['M0', 'M1', 'M6', 'M4', 'M4S', 'TB']):
            o = KO[k].get(m)
            if not o: continue
            sat.append([f'{KAT_TARIH[int(k)]} (n = {n(o["n"])})' if j == 0 else '', m, Y(o['gk_yanlilik']), Y(o['gk_wape']),
                        F(o['kiyas_sapma']) if m != 'TB' else TIRE, Y(o.get('t_yanlilik')), F(o['maliyet90'], 2)])
    dg = g('S_orta', 'gunluk_degisim') or {}
    deg = ', '.join(f'{KAT_TARIH[int(k)]} {Y(v, 1, True)}' for k, v in sorted(dg.items(), key=lambda x: int(x[0])))
    return ('Başlangıç noktalarına göre ölçütler (orta sansür şiddeti)',
            ['Başlangıç', 'Model', 'GY', 'GAMH', 'KS', 'Test yanlılığı', 'Maliyet (k = 0,90)'], sat,
            f'Başlangıç noktaları 2026 yılına aittir. Test penceresindeki günlük ortalama gerçek talebin eğitim penceresine göre değişimi: {deg}.')

def t_dilim():
    sat = []
    for d in g('S_orta', 'sansur_dilim') or []:
        et = '%0' if d['ust'] == 0 else f'{">%0" if d["alt"] == 0 else Y(d["alt"])} – {Y(d["ust"])}'
        sat.append(['Sansürlü gün oranı ' + et, n(d['n'])] + [Y(d[m]['gk_yanlilik']) + ' / ' + Y(d[m]['gk_wape']) for m in ['M0', 'M1', 'M2', 'M6', 'M4', 'TB']])
    for d in g('S_orta', 'ota_dilim') or []:
        et = f'{f(d["alt"], 2)} – {f(d["ust"], 2) if d["ust"] < 1e6 else "∞"}'
        sat.append(['Ortalama talep aralığı ' + et, n(d['n'])] + [(Y(d[m]['gk_yanlilik']) + ' / ' + Y(d[m]['gk_wape'])) if m in d else TIRE
                                                                for m in ['M0', 'M1', 'M2', 'M6', 'M4', 'TB']])
    return ('Seri dilimlerine göre geri kazanım yanlılığı ve GAMH (orta sansür şiddeti)',
            ['Dilim', 'Seri-başlangıç', 'M0', 'M1', 'M2', 'M6', 'M4', 'TB'], sat,
            'Hücrelerde GY / GAMH verilmiştir. Pozitif sansür oranlı seriler medyan ve 0,80 yüzdeliğinden üç dilime ayrılmıştır. '
            'Ortalama talep aralığı dilimlerinde 1,32 eşiği aralıklı talep sınıflandırmasından alınmıştır.')

def t_olasiliksal():
    O = g('S_orta', 'olcut') or {}; PIT = g('S_orta', 'pit') or {}
    sat = []
    for m in modeller(O):
        o = O[m]
        pit = PIT.get(m)
        pits = TIRE
        if pit:
            t = sum(pit); pits = ' '.join(f'{100 * v / t:.0f}' for v in pit)
        sat.append([m, F(o['crps']), Y(o['kapsama80']), F(o['genislik80'], 2), F(o['pinball90']), Y(o['t_yanlilik'], 1, True), pits])
    return ('Test penceresinde olasılıksal tahmin ölçütleri ve PIT dağılımı (orta sansür şiddeti)',
            ['Model', 'SSOS', '%80 kapsama', 'Aralık genişliği', 'Kantil kaybı (0,90)', 'Test talebi yanlılığı', 'PIT onda birlik dilim payları (%)'], sat,
            'PIT, test penceresinin gerçek toplam talebindeki birikimli olasılıktır, F(y). Talep kesikli ve çoğunlukla sıfır olduğu için F(y) düzgün dağılmamakta ve üst dilimlerde toplanmaktadır. '
            'Kalibrasyon bu yüzden gerçek test talebiyle kurulan TK modelinin dağılımıyla karşılaştırılarak okunmaktadır. Aralık genişliği test penceresinin gerçek toplam talebine bölünmüştür.')

def t_parametre():
    sat = []
    sk = g('S_orta', 'skaler') or {}
    for k in sorted(sk, key=int):
        s = sk[k]
        sat.append([KAT_TARIH[int(k)], F(s.get('M4_phi'), 2), F(s.get('M4S_phi'), 2), F(s.get('M4D_phi'), 2), F(s.get('M4H_phi'), 2), F(s.get('TB_phi'), 2),
                    f'{s.get("M4_em_tur")}, {s.get("M4H_em_tur")}, {s.get("M4K_em_tur")}', n(s.get('M3_sinir') or 0), str(s.get('m2_w')), f(s.get('m6_alfa') or 0, 2),
                    f'{n(s.get("denetim_n") or 0)}, {Y(s.get("a_hat"))}'])
    return ('Orta sansür şiddetinde tahmin edilen parametreler ve çözüm bilgisi',
            ['Başlangıç', 'ϕ M4', 'ϕ M4S', 'ϕ M4D', 'ϕ M4H', 'ϕ TB', 'Yineleme', 'M3 sınır', 'M2 w', 'M6 α', 'Denetim n, a'], sat,
            'Başlangıç noktaları 2026 yılına aittir. ϕ seri çarpanının varyansıdır. Yineleme sütunu M4, M4H ve M4K çözümlerinin yineleme sayısını vermektedir ve 200 değeri en iyilemenin yineleme sınırında durduğunu belirtmektedir. M2 w ve M6 α değerleri ayar kümelerinin alt ucundadır. '
            'M3 sınır çözümü, seri içi olabilirliğin arama aralığının üst sınırında en büyüklendiği seri sayısıdır.')

def t_aprofil():
    sat = []
    aday = ['0', '0,05', '0,10', '0,20', '0,35', '0,50']
    def satir(ad, prof):
        for k in sorted(prof, key=int):
            v = prof[k]
            if not v: continue
            sat.append([ad if k == sorted(prof, key=int)[0] else '', KAT_TARIH[int(k)]] + [f(x - v[0], 1) for x in v])
    if g('S_orta', 'a_profil'): satir('Gürültüsüz', g('S_orta', 'a_profil'))
    for t, ad in [('FP05', 'Yanlış pozitif 0,05'), ('FP10', 'Yanlış pozitif 0,10'), ('FP20', 'Yanlış pozitif 0,20')]:
        pr = g('gurultu', t, 'a_profil')
        if pr: satir(ad, pr)
    return ('Etiket hatası payı a için profil log olabilirlik (a = 0 değerine göre fark)',
            ['Senaryo', 'Başlangıç'] + [f'a = {x}' for x in aday], sat,
            'Değerler M4 çözümünün β katsayıları sabit tutulup ϕ her a değeri için yeniden en büyüklenerek hesaplanmıştır. Bütün satırlarda olabilirlik a arttıkça azalmaktadır ve en büyük değer a = 0 sınırındadır. '
            'Sansürlü bileşen P(D ≥ y) stok düzeyinin olasılığını içermediği için bu davranış olabilirliğin yapısından gelmektedir ve gerçek yanlış pozitif payı sıfırdan büyük olduğunda da değişmemektedir.')

def t_pencere():
    sat = []
    for s, ad in [('S_orta_L56', '56 gün'), ('S_orta', '112 gün'), ('S_orta_L999', 'Bütün geçmiş')]:
        O = g(s, 'olcut') or {}
        for j, m in enumerate([m for m in ['M0', 'M1', 'M6', 'M4', 'M4S', 'TB'] if m in O]):
            o = O[m]
            sat.append([f'{ad} (n = {n(g(s, "n_gozlem") or 0)})' if j == 0 else '', m, Y(o['gk_yanlilik']), Y(o['gk_wape']),
                        F(o['kiyas_sapma']) if m != 'TB' else TIRE, F(o['crps']), F(o['maliyet90'], 2)])
    return ('Eğitim penceresi uzunluğuna duyarlılık (orta sansür şiddeti)',
            ['Eğitim penceresi', 'Model', 'GY', 'GAMH', 'KS', 'SSOS', 'Maliyet (k = 0,90)'], sat,
            'Bütün geçmiş, başlangıç noktasından önceki bütün günleri kapsamaktadır. Seri seçim kuralları her pencerede aynıdır.')

def t_filtre():
    sat = []
    E = g('S_orta', 'eski_filtre') or {}; O = g('S_orta', 'olcut') or {}
    for m in [m for m in ['M0', 'M1', 'M2', 'M6', 'M4', 'M4S', 'TB'] if m in E]:
        sat.append([m, Y(O[m]['gk_yanlilik']), Y(E[m]['gk_yanlilik']), Y(O[m]['gk_wape']), Y(E[m]['gk_wape']),
                    F(O[m]['kiyas_sapma']) if m != 'TB' else TIRE, F(E[m]['kiyas_sapma']) if m != 'TB' else TIRE])
    return ('Seri seçim kuralına duyarlılık: test penceresinde en az bir ve en az yedi bilinen gün koşulu',
            ['Model', 'GY', 'GY (yedi gün)', 'GAMH', 'GAMH (yedi gün)', 'KS', 'KS (yedi gün)'], sat,
            f'Ana analiz {n(g("S_orta", "n_gozlem") or 0)} seri-başlangıç gözlemi, yedi gün koşulu {n(g("S_orta", "eski_filtre_n") or 0)} gözlem içermektedir. '
            'İki koşul da test penceresindeki stok durumuna dayanan ölçülebilirlik koşullarıdır ve ana analizde ölçütün hesaplanabilmesi için gereken en gevşek koşul olan bir gün koşulu uygulanmıştır.')

def t_dogal_tam():
    sat = []
    for cr, ad in [('CR1', 'SR1'), ('CR2', 'SR2'), ('CR3', 'SR3'), ('CR4', 'SR4'), ('CR5', 'SR5')]:
        O = g(f'D_{cr}', 'olcut') or {}
        for j, m in enumerate(modeller(O)):
            o = O[m]; kt = o.get('kayip_talep_orani')
            sat.append([ad if j == 0 else '', m, ARALIK(kt) if kt else TIRE, Y(o['t_yanlilik_satis'], 1, True), Y(o['t_wape_satis']),
                        Y(o['t_yanlilik_stoklu'], 1, True), F(o['crps_satis'])])
    return ('Doğal veride bütün modellerin kayıp talep oranı ve test penceresindeki satışa uzaklığı',
            ['Tanım', 'Model', 'Kayıp talep oranı (%95 aralık)', 'Satışa göre yanlılık', 'Satışa göre GAMH', 'Stoklu günlerde yanlılık', 'SSOS (satış)'], sat,
            'Test penceresindeki satış, stok tükenmesi nedeniyle talebin alt sınırıdır. Stoklu günler sütunu, test penceresinde gün sonu stoku pozitif kalan günlerle sınırlıdır ve bu seçim satışın stoku bitirmediği, görece düşük talepli günleri öne almaktadır. '
            'Sansürü kullanmayan M0 ve M4S için kayıp talep oranı tanımlı tutulmamıştır.')

def t_m4z():
    O = g('S_orta', 'olcut') or {}; K = g('S_orta', 'karsilastirma') or {}
    sat = []
    for m in [m for m in ['M4', 'M4Z', 'M4D', 'M4R'] if m in O]:
        o = O[m]
        sat.append([m, Y(o['gk_yanlilik']), Y(o['gk_wape']), F(o['kiyas_sapma']), F(o['crps']), F(o['maliyet90'], 2),
                    TIRE if m == 'M4' else YILDIZ(K.get('kiyas_sapma', {}).get(m))])
    return ('M4 ailesinin sürümleri (orta sansür şiddeti)',
            ['Model', 'GY', 'GAMH', 'KS', 'SSOS', 'Maliyet (k = 0,90)', 'KS farkı (M4 − model)'], sat,
            'Sürümler M4 çözümünden başlatılmış ve en çok 100 yinelemeyle çözülmüştür. * Holm düzeltmeli p < 0,05.')

TUM = {'ana_olcut': t_ana_olcut, 'karsilastirma': t_karsilastirma, 'heterojenlik': t_heterojenlik, 'gurultu': t_gurultu,
       'karar': t_karar, 'dogal': t_dogal, 'siddet': t_siddet, 'karsilastirma_tam': t_karsilastirma_tam, 'kat': t_kat,
       'dilim': t_dilim, 'olasiliksal': t_olasiliksal, 'parametre': t_parametre, 'aprofil': t_aprofil, 'pencere': t_pencere,
       'filtre': t_filtre, 'dogal_tam': t_dogal_tam, 'm4z': t_m4z}
