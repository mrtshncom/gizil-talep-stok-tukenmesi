# -*- coding: utf-8 -*-
"""Bulgular, tartışma ve sonuç. Sayılar ve hipotez kararları analiz çıktılarından okunur.
Atıflı cümlelerin pasajları kaynağın kayıtlı özet metninde birebir aranır (kanit.py)."""
from sayilar import *

def O(m): return (m, None, None, None)
def A(m, k, pasaj, konum='özet'): return (m, k, pasaj, konum)

S = R['S_orta']; OL = S['olcut']; K = S['karsilastirma']; KA = S['ks_ayristirma']; HT = S['heterojenlik']; DL = S['sansur_dilim']
SEV = ['S_dusuk', 'S_orta', 'S_yuksek']
def gy(s, m): return R[s]['olcut'][m]['gk_yanlilik']
def ol(m, o, s='S_orta'): return R[s]['olcut'][m][o]
def ph(o, m): return K[o][m]['p_holm']
def fk(o, m): return K[o][m]['fark']
KIYAS = ['M0', 'M1', 'M2', 'M3', 'M5', 'M6']
def anlamli(o, ms): return [m for m in ms if K[o][m]['p_holm'] < 0.05 and K[o][m]['fark'] < 0]
def liste(ms):
    ms = list(ms)
    return ms[0] if len(ms) == 1 else ', '.join(ms[:-1]) + ' ve ' + ms[-1]
def karar(b): return 'desteklenmiştir' if b else 'desteklenmemiştir'
def S_ref(k): return '{S:' + k + '}'
def T_ref(k): return '{T:' + k + '}'
def EK_ref(k): return '{EK:' + k + '}'

_sifir_talep = S['sansurlu_sifir_talep'] / S['sansurlu_gun']
_deg = [S['gunluk_degisim'][k] for k in sorted(S['gunluk_degisim'], key=int)]
_ci0 = {s: R[s]['ci']['M0']['gk_yanlilik'] for s in SEV}
H1 = all(gy(SEV[j + 1], 'M0') < gy(SEV[j], 'M0') for j in range(2)) and _ci0['S_yuksek']['ust'] < 0
_gy_an = anlamli('gk_yanlilik_mutlak', KIYAS); _gy_ns = [m for m in KIYAS if m not in _gy_an]
H2a = len(_gy_ns) == 0
_ks_an = anlamli('kiyas_sapma', KIYAS); H2b = len(_ks_an) == len(KIYAS)
_hi = HT['ad'].index('bayrak_orani'); H3 = HT['katsayi'][_hi] > 0 and HT['p'][_hi] < 0.05
_c4 = S['ci']['M4']
_cost_m0 = K['maliyet90']['M0']; _cost_s = K['maliyet90']['M4S']
H5_m0 = _cost_m0['fark'] < 0 and _cost_m0['p_holm'] < 0.05
H5_s = _cost_s['fark'] < 0 and _cost_s['p_holm'] < 0.05
_kap = OL['M4']['pisman_TB90'] / OL['M0']['pisman_TB90']
import math

def _m4z_sinir():
    import numpy as _np
    try:
        return all(int(_np.load(os.path.join(CIKTI, 'deney', f'S_ortaZ_k{k}.npz'))['M4Z_em_tur']) >= 100 for k in range(4))
    except (OSError, KeyError):
        return False
_ust_sinir = math.ceil(max(abs(gy(s, 'M4')) for s in SEV) * 200) / 200

# ek sınamalar
_RT = ES['ortalamaya_donus']; _tek = sum(x['tek_birim_payi'] for x in _RT) / len(_RT)
_KH = ES['kiyas_havuzsuz']; _SZ = ES['sifir_stok']
_ks_en = min(KIYAS, key=lambda m: ol(m, 'kiyas_sapma'))
_tw_ust = all(_KH['M4']['test_wape'] < _KH[m]['test_wape'] for m in KIYAS)
_ph = ES['izgara']['m4h_phi']
H5 = H5_m0 and H5_s
_kap_s = OL['M4S']['pisman_TB90'] / OL['M0']['pisman_TB90']

# etiket gürültüsü
GU = R.get('gurultu', {})
def ggy(t, m): return GU[t][m]['gk_yanlilik'] if t in GU and m in GU[t] else None
_gur_var = all(t in GU for t in ['FN05', 'FN10', 'FN20', 'FP05', 'FP10', 'FP20'])
if _gur_var:
    _fn = [ggy(f'FN{e}', 'M4') for e in ('05', '10', '20')]; _fp = [ggy(f'FP{e}', 'M4') for e in ('05', '10', '20')]
    _g0 = gy('S_orta', 'M4')
    H4a = all(x < _g0 for x in _fn) and all(x > _g0 for x in _fp)
    _fpd = GU.get('FP20_fark', {}).get('gk_yanlilik')
    H4b = bool(_fpd) and _fpd['fark'] < 0 and _fpd['ust'] < 0
    _ah = [v for v in GU['FP20']['a_hat'].values() if v is not None]; _ah20 = sum(_ah) / len(_ah)
    _sens = [ggy('FP20', m) - gy('S_orta', m) for m in ('M1', 'M2', 'M6', 'M4')]

# doğal veri
DN_ = {cr: R.get(f'D_{cr}') for cr in ['CR1', 'CR2', 'CR3', 'CR4', 'CR5']}
_dog_var = all(DN_.values())
if _dog_var:
    def kt(cr, m): return DN_[cr]['olcut'][m]['kayip_talep_orani']['deger']
    _kt4 = {cr: kt(cr, 'M4') for cr in DN_}
    _ktmin = min(_kt4, key=_kt4.get); _ktmax = max(_kt4, key=_kt4.get)
    _sr = {cr: DN_[cr]['sansur_orani'] for cr in DN_}
TAN = {'CR1': 'SR1', 'CR2': 'SR2', 'CR3': 'SR3', 'CR4': 'SR4', 'CR5': 'SR5'}

# pencere
_L = {L: R.get(f'S_orta_L{L}') for L in ('56', '999')}
_pen_var = all(_L.values())

SONUC = [
 ('h1', '4. Bulgular'),
 ('h2', '4.1. Analiz kümesi ve test dönemindeki talep değişimi'),
 ('p', [
  O(f'Orta sansür şiddetinde analiz kümesi {n(S["n_magaza"])} mağazadan {n(S["n_seri"])} seriyi ve dört başlangıç noktasında {n(S["n_gozlem"])} seri-başlangıç gözlemini içermektedir.'),
  O(f'Eğitim penceresindeki seri-günlerin {yz(S["sansur_orani"])} kadarı sansürlü olarak işaretlenmiştir ve sansürlü günlerde kaybolan talep gerçek eğitim talebinin {yz(S["kayip_payi"])} kadarına karşılık gelmektedir.'),
  O(f'Sansürlü günlerin {yz(_sifir_talep)} kadarında gerçek talep sıfırdır, kayıp talep sansürlü günlerin küçük bir bölümünde toplanmaktadır.'),
  O(f'Düşük ve yüksek şiddette sansürlü gün oranı {yz(R["S_dusuk"]["sansur_orani"])} ve {yz(R["S_yuksek"]["sansur_orani"])}, kayıp talep payı {yz(R["S_dusuk"]["kayip_payi"])} ve {yz(R["S_yuksek"]["kayip_payi"])} düzeyindedir.'),
 ]),
 ('p', [
  O(f'Test penceresindeki günlük ortalama talep, dört başlangıç noktasında eğitim penceresine göre {yz(_deg[0], 0)}, {yz(_deg[1], 0)}, {yz(_deg[2], 0)} ve {yz(_deg[3], 0)} değişmiştir.'),
  O(f'Aynı başlangıç noktalarında eğitimde en az 28, testte en az bir bilinen günü olan bütün serilerde değişim {yz(_RT[0]["evren_degisim"], 0, True)}, {yz(_RT[1]["evren_degisim"], 0, True)}, {yz(_RT[2]["evren_degisim"], 0, True)} ve {yz(_RT[3]["evren_degisim"], 0, True)} olmuştur.'),
  O(f'Seçim kuralı eğitim penceresinde en az bir birim satış istemektedir ve seçilen serilerin {yz(_tek, 0)} kadarı eğitim penceresinin 112 gününde yalnız bir birim satmıştır.'),
  O('Eğitimdeki rastlantısal satışla seçilen seyrek seriler test penceresinde ortalamaya dönmekte ve test dönemindeki düşüşün büyük bölümü takvimden çok bu seçimden kaynaklanmaktadır.'),
  O('Eğitim düzeyini test penceresine aktaran modeller talebi fazla tahmin etmektedir, büzülme uygulayan havuzlu modellerde fazla tahmin küçülmektedir.'),
  O(f'Gerçek eğitim talebiyle kurulan TB modeli de test penceresinde talebi {yz(ol("TB", "t_yanlilik"), 1, True)} fazla tahmin etmektedir.'),
  O('Test penceresinin gerçek talebine uzaklık sansür düzeltmesinin katkısını seçim kaynaklı düzey değişiminden ayıramamaktadır, sansür düzeltmesinin tahmine katkısı TB modeline uzaklıkla, yani kıyas sapmasıyla ölçülmekte ve gerçek test talebine uzaklık ikincil ölçüt olarak raporlanmaktadır.'),
  O('Bütün modellerin ölçütleri {T:ana_olcut} içinde, M4 modelinin eşleştirilmiş karşılaştırmaları {T:karsilastirma} içinde verilmiştir.'),
 ]),
 ('table', 'ana_olcut'),

 ('h2', '4.2. Sansür şiddeti ve satışı talep sayan model (AS1, H1)'),
 ('p', [
  O(f'M0 modelinin geri kazanım yanlılığı düşük, orta ve yüksek şiddette sırasıyla {yz(gy("S_dusuk", "M0"))}, {yz(gy("S_orta", "M0"))} ve {yz(gy("S_yuksek", "M0"))} olmuştur ({S_ref("sekil2_siddet")}).'),
  O(f'Yüksek şiddetteki %95 önyükleme aralığı {yz(_ci0["S_yuksek"]["alt"])} – {yz(_ci0["S_yuksek"]["ust"])} olup sıfırı içermemektedir.'),
  O(f'M0 modelinin yanlılığı her senaryoda kayıp talep payına eşittir, model sansürlü günde talebi satış kadar kabul ettiği için kayıp talebin tamamı yanlılığa geçmektedir.'),
  O(f'M4 modelinin yanlılığı aynı senaryolarda {yz(gy("S_dusuk", "M4"))}, {yz(gy("S_orta", "M4"))} ve {yz(gy("S_yuksek", "M4"))} düzeyinde kalmış ve şiddetle büyümemiştir.'),
  O(f'H1 {karar(H1)}.'),
  O('Bütün modellerin şiddete göre ölçütleri {EK:siddet} içinde verilmiştir.'),
 ]),
 ('fig', 'sekil2_siddet', 'Sansür şiddetine göre eğitim penceresindeki geri kazanım yanlılığı. Yatay eksen her senaryonun sansürlü gün oranıdır.'),

 ('h2', '4.3. Havuzlu sansürlü modelin geri kazanımı (AS2, H2)'),
 ('p', [
  O(f'Orta şiddette M4 modelinin geri kazanım yanlılığı {yz(_c4["gk_yanlilik"]["deger"])} (%95 aralık {yz(_c4["gk_yanlilik"]["alt"])} – {yz(_c4["gk_yanlilik"]["ust"])}) olarak bulunmuştur.'),
  O(f'Mutlak yanlılıkta M4 modeli {liste(_gy_an)} modellerinden Holm düzeltmeli 0,05 düzeyinde düşük hata vermiştir.'
    + (f' {liste(_gy_ns)} karşısındaki fark ise düzeltmeden sonra anlamlılık sınırını geçememiştir.' if _gy_ns else '')),
  O(f'M1 silme yaklaşımının yanlılığı {yz(ol("M1", "gk_yanlilik"))}, M6 sansürlü üstel düzeltmenin yanlılığı {yz(ol("M6", "gk_yanlilik"))} düzeyindedir.'),
  O(f'H2a {karar(H2a)}' + (', M4 modelinin toplam talepteki üstünlüğü kıyas modellerinin tamamına yayılmamaktadır.' if not H2a else '.')),
 ]),
 ('p', [
  O(f'Seri düzeyindeki mutlak hatada (GAMH) M4 modeli {yz(ol("M4", "gk_wape"))} ile {liste(anlamli("gk_wape", KIYAS))} modellerinden düşük hata vermiştir.'),
  O(f'M0 karşısındaki GAMH farkı {f(fk("gk_wape", "M0"), 3)} birimdir ve Holm düzeltmeli olasılık değeri {f(ph("gk_wape", "M0"), 3)} düzeyindedir.'),
  O(f'Ortalama tamamlama yerine medyan tamamlama kullanıldığında M4 modelinin GAMH değeri {yz(ol("M4", "gk_wape_medyan"))} düzeyine inmekte ve {"M0 dahil bütün kıyas modellerinden" if len(anlamli("gk_wape_medyan", KIYAS)) == len(KIYAS) else liste(anlamli("gk_wape_medyan", KIYAS)) + " modellerinden"} anlamlı düşüklükte kalmaktadır.'),
  O('Ortalama tamamlama sıfır talepli sansürlü günlere pozitif beklenen talep atadığı için seri düzeyindeki mutlak hatayı büyütmektedir, seri toplamındaki küçük beklenen fazla medyan tamamlamada sıfıra yuvarlanmaktadır.'),
  O('Medyan tamamlamalı sürüm önceden belirlenmiş ölçütlerin dışında olduğu için bu sonuç keşifsel olarak okunmaktadır.'),
  O(f'Düşük şiddette M4 modelinin GAMH değeri ({yz(ol("M4", "gk_wape", "S_dusuk"))}) M0 ({yz(ol("M0", "gk_wape", "S_dusuk"))}) ve M1 ({yz(ol("M1", "gk_wape", "S_dusuk"))}) modellerinin üstündedir ve seri düzeyindeki kazanç sansür şiddetiyle birlikte ortaya çıkmaktadır.'),
 ]),
 ('p', [
  O(f'Test penceresinde M4 modelinin kıyas sapması {f(_c4["kiyas_sapma"]["deger"], 3)} (%95 aralık {f(_c4["kiyas_sapma"]["alt"], 3)} – {f(_c4["kiyas_sapma"]["ust"], 3)}) olmuştur.'),
  O(f'Aynı ölçütte kıyas kümesinin en düşük değeri {_ks_en} modelinin {f(ol(_ks_en, "kiyas_sapma"), 3)} değeridir ve M4 {"bütün kıyas modellerinden" if H2b else liste(_ks_an) + " modellerinden"} Holm düzeltmeli 0,05 düzeyinde düşük sapma vermiştir.'),
  O(f'H2b {karar(H2b)}.'),
  O('TB modeli M4 mimarisiyle kurulduğu için bu karar mimariye koşulludur: KS, sansür düzeltmesinin yanında TB yapısının ne kadar kopyalandığını da ölçmektedir.'),
  O(f'Gerçek test talebine göre ağırlıklı mutlak hatada M4 modeli {f(_KH["M4"]["test_wape"], 3)} değeriyle ' + ('kıyas kümesinin bütün modellerinden düşük kalmakta' if _tw_ust else 'kıyas kümesinin bazı modellerinin üstünde kalmakta') + f', M4S modeli ise {f(_KH["M4S"]["test_wape"], 3)} ile M4 modelinden düşük hata vermektedir.'),
  O(f'M0 ile M4 arasındaki {f(KA["toplam"], 3)} birimlik kıyas sapması farkının {yz(KA["mimari_pay"])} kadarı (%95 aralık {yz(KA["mimari_pay_alt"])} – {yz(KA["mimari_pay_ust"])}) havuzlu mimariden, {yz(KA["sansur_pay"])} kadarı sansür düzeltmesinden gelmektedir ve bu ayrıştırma da TB kıyasının mimarisine koşulludur.'),
  O(f'Sansür düzeltmesi, havuzlu mimarinin sansürü yok sayan sürümü M4S karşısında kıyas sapmasını {yz(KA["sansur_marjinal"])} azaltmıştır.'),
  O(f'Seri içi sansürlü olabilirlik (M3) {n(S["M3_sinir"])} seri-başlangıç gözleminde arama aralığının üst sınırında çözülmüş ve {yz(ol("M3", "gk_yanlilik"), 0, True)} yanlılık üretmiştir, seyrek seride havuzlama yapılmadığında sansürlü olabilirlik kararsız kalmaktadır.'),
 ]),
 ('p', [
  O(f'Olasılıksal ölçütlerde M4 modeli kıyas modellerinden düşük SSOS değeri vermiştir, M4S modelinin SSOS değeri ise M4 modelinden {f(fk("crps", "M4S"), 4)} birim düşüktür.'),
  O(f'M4S eğitim düzeyini aşağı yönlü tahmin etmekte ve test penceresinde talebi {yz(ol("M4S", "t_yanlilik"), 1, True)} yanlılıkla tahmin etmektedir, bu düşük düzey seçilen serilerin test penceresindeki ortalamaya dönüşüyle örtüşmektedir.'),
  O(f'%80 tahmin aralıklarında bütün modellerde aşırı kapsama görülmektedir (M4 için {yz(ol("M4", "kapsama80"))}), çünkü test toplam talebi gözlemlerin {yz(ES["test_talep_sifir"], 0)} kadarında sıfırdır ve düşük hacimli kesikli talepte aralığın alt ucu sıfıra yerleşmektedir.'),
  O('Başlangıç noktalarına göre ölçütler {EK:kat}, bütün karşılaştırmalar {EK:karsilastirma_tam}, olasılıksal ölçütler {EK:olasiliksal} ve tahmin edilen parametreler {EK:parametre} içinde verilmiştir.'),
 ]),
 ('table', 'karsilastirma'),

 ('h2', '4.4. Sansür oranına göre kazanç (AS3, H3)'),
 ('p', [
  O(f'Sansürlü gün oranı sıfır olan {n(DL[0]["n"])} gözlemde bütün modeller gözlenen satışı değiştirmemekte ve yanlılık sıfırdır.'),
  O(f'Pozitif sansür oranlı gözlemler, sansür oranının medyanı ({yz(DL[1]["ust"])}) ve 0,80 yüzdeliği ({yz(DL[2]["ust"])}) ile üç dilime ayrılmıştır.'),
  O(f'Pozitif sansür oranlı serilerde M0 modelinin yanlılığı alt, orta ve üst dilimlerde {yz(DL[1]["M0"]["gk_yanlilik"])}, {yz(DL[2]["M0"]["gk_yanlilik"])} ve {yz(DL[3]["M0"]["gk_yanlilik"])} düzeyine inmekte, M4 modelinin yanlılığı ise {yz(DL[1]["M4"]["gk_yanlilik"])}, {yz(DL[2]["M4"]["gk_yanlilik"])} ve {yz(DL[3]["M4"]["gk_yanlilik"])} aralığında kalmaktadır ({S_ref("sekil3_dilim")}).'),
  O(f'Seri düzeyindeki mutlak hatada M4 modeli en düşük dilimde M0 modelinden yüksek ({yz(DL[1]["M4"]["gk_wape"])} ve {yz(DL[1]["M0"]["gk_wape"])}), en yüksek dilimde düşük ({yz(DL[3]["M4"]["gk_wape"])} ve {yz(DL[3]["M0"]["gk_wape"])}) hata vermektedir.'),
 ]),
 ('fig', 'sekil3_dilim', 'Serinin eğitim penceresindeki sansürlü gün oranına göre geri kazanım yanlılığı (orta sansür şiddeti)'),
 ('p', [
  O(f'Heterojenlik regresyonunda sansürlü gün oranının katsayısı {f(HT["katsayi"][_hi], 3)} (kümelenmiş SH {f(HT["se"][_hi], 3)}, {p(HT["p"][_hi])}) olarak tahmin edilmiştir ({T_ref("heterojenlik")}).'),
  O(f'Gözlenen satış hacminin logaritması da pozitif katsayı almıştır ({f(HT["katsayi"][4], 3)}, {p(HT["p"][4])}), kazanç birim cinsinden ölçüldüğü için hacimli serilerde büyümektedir.'),
  O(f'Ortalama talep aralığı ve talep büyüklüğünün değişkenliği pozitif ve anlamlı katsayılar almıştır, modelin açıklama gücü düşüktür (R² = {f(HT["r2"], 3)}).'),
  O('Bu iki değişken gözlenen satıştan hesaplandığı için sansür oranıyla mekanik bir bağ taşıyabilmektedir ve katsayıları keşifsel olarak okunmaktadır.'),
  O(f'Sabit terim ({f(HT["katsayi"][0], 3)}) gözlenen satışın sıfır olduğu ve seçim kuralı gereği veride bulunmayan bir noktaya karşılık geldiği için yorumlanmamaktadır.'),
  O(f'Sansürsüz {n(DL[0]["n"])} gözlemde bağımlı değişken tanım gereği sıfırdır ve bu gözlemler sansür oranı katsayısını sıfır noktasında sabitlemektedir, dilim sonuçları regresyonla birlikte okunmaktadır.'),
  O(f'H3 {karar(H3)}.'),
  O('Dilim sonuçlarının tamamı {EK:dilim} içinde verilmiştir.'),
 ]),
 ('table', 'heterojenlik'),

 ('h2', '4.5. Stok etiketi hatası (AS4, H4)'),
] + ([
 ('p', [
  O(f'Yanlış negatif hata oranı 0,05, 0,10 ve 0,20 olduğunda M4 modelinin yanlılığı {yz(_fn[0])}, {yz(_fn[1])} ve {yz(_fn[2])}, yanlış pozitif hata altında {yz(_fp[0])}, {yz(_fp[1])} ve {yz(_fp[2])} olmuştur ({S_ref("sekil4_gurultu")}, {T_ref("gurultu")}).'),
  O('Yanlış negatif hata kayıp talebi görünmez kılarak yanlılığı aşağı, yanlış pozitif hata talebi tam gözlenen günleri alt sınır sayarak yanlılığı yukarı çekmektedir.'),
  O(f'Etkinin büyüklüğü taban oranlarla açıklanmaktadır: yanlış pozitif hata günlerin {yz(1 - S["sansur_orani"])} kadarı olan sansürsüz günlere eklendiği için %20 hata düzeyinde bayraklı gün oranını {yz(GU["FP20"]["sansur_orani"])} düzeyine çıkarmakta, yanlış negatif hata ise yalnız {yz(S["sansur_orani"])} kadarlık sansürlü günlerden bayrak kaldırmaktadır.'),
  O(f'%20 yanlış pozitif hatada gürültüsüz duruma göre yukarı kayma M1, M2, M6 ve M4 modellerinde sırasıyla {f(_sens[0] * 100, 1)}, {f(_sens[1] * 100, 1)}, {f(_sens[2] * 100, 1)} ve {f(_sens[3] * 100, 1)} yüzde puandır, '
    f'seri içi modeller M3 ve M5 ise {yz(ggy("FP20", "M3"), 0, True)} ve {yz(ggy("FP20", "M5"), 0, True)} yanlılığa ulaşmaktadır.'),
  O(f'H4a {karar(H4a)}.'),
 ]),
 ('p', [
  O(f'%20 yanlış pozitif hatada denetim örneklemi, bayraklı günlerin ortalama {yz(_ah20)} kadarının gerçekte sansürsüz olduğunu belirlemiştir.'),
  O(f'Bu hata düzeyinde M4R modelinin mutlak yanlılığı M4 modelinden {f(-_fpd["fark"], 3)} birim düşüktür (fark {f(_fpd["fark"], 3)}, %95 aralık {f(_fpd["alt"], 3)} – {f(_fpd["ust"], 3)}).') if _fpd else O(''),
  O(f'Yanlış pozitif hata oranı 0,05, 0,10 ve 0,20 iken M4R modelinin yanlılığı {yz(ggy("FP05", "M4R"))}, {yz(ggy("FP10", "M4R"))} ve {yz(ggy("FP20", "M4R"))} olmuştur, model kaymayı gidermekte fakat aşağı yönde aşırı düzeltme yapmaktadır.'),
  O(f'Hata oranı 0,05 ve 0,10 iken M4R modelinin mutlak yanlılığı M4 modelinden yüksektir ({yz(abs(ggy("FP05", "M4R")))} ve {yz(abs(ggy("FP05", "M4")))}, {yz(abs(ggy("FP10", "M4R")))} ve {yz(abs(ggy("FP10", "M4")))}), düzeltmenin kazancı yalnız %20 hata düzeyinde ortaya çıkmaktadır.'),
  O(f'Aşırı düzeltmenin kaynağı tek bir hata payının bütün bayraklı günlere uygulanmasıdır: %20 hata düzeyinde bayraklı günlerin gerçekte sansürsüz olan payı satışı sıfır olan günlerde {yz(ES["fp_satis_durumu"]["FP20"]["y0"])}, satışlı günlerde {yz(ES["fp_satis_durumu"]["FP20"]["y1"])} düzeyindedir.'),
  O('Model satışlı bayraklı günlere gerçekte olduğundan yüksek bir sansürsüz olasılığı atamakta ve yukarı yönlü düzeltmeyi bilgi taşıyan bu günlerde geri çekmektedir, hata payının satış durumuna göre ayrı denetlenmesi bu yanlış belirlemeyi gidermeye adaydır.'),
  O('Yanlış negatif senaryolarda denetim örneklemi bayraklı günlerde hata bulamamakta ve M4R modeli M4 modeliyle aynı çözümü vermektedir, bayraksız günlerdeki hatayı öğrenmek bayraksız günlerin de denetlenmesini gerektirmektedir.'),
  O(f'H4b {karar(H4b)}.'),
  O('Profil olabilirlik bütün senaryolarda hata payı arttıkça azalmış ve en büyük değerini sıfır sınırında almıştır ({EK:aprofil}).'),
  O('Sansürlü bileşen stok düzeyinin olasılığını içermediği için bu davranış olabilirliğin yapısından gelmektedir, bu yapıda hata payı satış ve bayrak verisinden tahmin edilememekte ve dışsal denetimden alınmaktadır.'),
 ]),
] if _gur_var else [('p', [O('Etiket gürültüsü sonuçları hazırlanmaktadır.')])]) + [
 ('fig', 'sekil4_gurultu', 'Stok etiketi gürültüsü altında geri kazanım yanlılığı. Sol panel yanlış negatif, sağ panel yanlış pozitif hatayı vermektedir.'),
 ('table', 'gurultu'),

 ('h2', '4.6. Yenileme politikasında maliyet ve pişmanlık (AS5, H5)'),
 ('p', [
  O(f'Hizmet düzeyi 0,90 iken M4 modelinin talep birimi başına maliyeti {f(ol("M4", "maliyet90"), 2)}, TK modeline göre pişmanlığı {f(ol("M4", "pisman_TK90"), 2)} birimdir ({T_ref("karar")}).'),
  O(f'M0 modelinin pişmanlığı {f(ol("M0", "pisman_TK90"), 2)} birimdir ve M4 ile arasındaki {f(-_cost_m0["fark"], 2)} birimlik fark Holm düzeltmeli 0,05 düzeyinde anlamlıdır.'),
  O(f'M4S modelinin pişmanlığı {f(ol("M4S", "pisman_TK90"), 2)} birimdir ve M4 ile arasındaki farkın ({f(_cost_s["fark"], 3)}) Holm düzeltmeli olasılık değeri {f(_cost_s["p_holm"], 3)} düzeyindedir.'),
  O(f'H5 {karar(H5)}' + (': M4 modelinin maliyeti M0 karşısında anlamlı düşük' if H5_m0 else ': M4 modelinin maliyeti M0 karşısında anlamlı düşüklükte değildir') + (', M4S karşısında ise nokta tahmini M4S lehinedir.' if _cost_s['fark'] > 0 else ', M4S karşısındaki fark anlamlılık sınırını geçememiştir.')),
 ]),
 ('p', [
  O(f'Gerçek eğitim talebiyle kurulan TB modelinin pişmanlığı {f(ol("TB", "pisman_TK90"), 2)} birimdir ve TK karşısındaki pişmanlığın büyük bölümü sansürden kaynaklanmamaktadır, seçim kaynaklı düzey değişiminden ve TK modelinin test sonuçlarıyla kurulmasından kaynaklanmaktadır.'),
  O(f'TB modeline göre ölçüldüğünde M0 modelinin fazladan maliyeti {f(ol("M0", "pisman_TB90"), 2)}, M4 modelinin fazladan maliyeti {f(ol("M4", "pisman_TB90"), 2)} birimdir ve M4, M0 modelinin tam bilgiye göre kaybettiği maliyetin {yz(1 - _kap, 0)} kadarını geri kazanmaktadır.'),
  O(('Sansürü yok sayan M4S modeli aynı kaybın tamamını kapatıp TB modelinin maliyetinin altına indiği için' if _kap_s <= 0 else f'Sansürü yok sayan M4S modeli aynı kaybın {yz(1 - _kap_s, 0)} kadarını kapattığı için') + f' maliyetteki kazanç havuzlu mimariden gelmektedir, sansür düzeltmesi ise bu mimarinin üzerine {f(_cost_s["fark"], 3)} birimlik maliyet eklemektedir.'),
  O('M4S modelinin maliyetinin TB modelinin altında kalması, TB kıyasının da bu test döneminde bir maliyet alt sınırı olmadığını belirtmektedir.'),
  O(f'Hizmet düzeyi 0,90 iken hiç stok tutmayan politikanın maliyeti 9,00 birimdir, {liste([m for m in ["M0", "M1", "M2", "M3", "M5", "M6", "M4", "M4S", "TB"] if ol(m, "maliyet90") > 9.0])} modellerinin maliyeti bu sınırı aşmakta, diğer modellerin maliyeti sınırın altında fakat yakınında kalmaktadır.'),
  O(f'Yakınlığın nedeni seyrek talepte hedef stokun sıfıra inmesidir: hizmet düzeyi 0,90 iken M4 modeli gözlemlerin {yz(_SZ["M4"]["90"]["sifir_stok"])} kadarında dört haftanın tamamı için sıfır hedef stok belirlemekte, düzey 0,50 iken bu pay {yz(_SZ["M4"]["50"]["sifir_stok"])} düzeyine çıkmaktadır.'),
  O('Haftalık talebin sıfır olma olasılığı hizmet düzeyini aştığında hedef stok sıfır olmakta ve maliyet stoksuz politikanın maliyetine yaklaşmaktadır, tahmin aralıklarının aşırı kapsaması ile düşük karşılama oranı aynı serilerde birlikte görülmektedir.'),
  O(f'TK modelinin maliyeti {f(ol("TK", "maliyet90"), 2)} birimdir ve düşük hacimli talepte maliyetin büyük bölümü durağan olmayan talepten gelmektedir.'),
  O(f'Karşılama oranı hizmet düzeyi 0,90 iken M4 modelinde {yz(ol("M4", "karsilama90"))}, M0 modelinde {yz(ol("M0", "karsilama90"))}, M4S modelinde {yz(ol("M4S", "karsilama90"))} ve TK modelinde {yz(ol("TK", "karsilama90"))} olmuştur, M0 modeli talebi fazla tahmin ettiği için daha yüksek stokla daha yüksek karşılamaya ulaşmakta ve daha yüksek maliyete katlanmaktadır.'),
  O(f'Devirli stok düzeninde M4, M0 ve M4S modellerinin pişmanlığı {f(ol("M4", "pismand_TK90"), 2)}, {f(ol("M0", "pismand_TK90"), 2)} ve {f(ol("M4S", "pismand_TK90"), 2)}, ölçekli tahmin düzeninde {f(ol("M4", "pismang_TK90"), 2)}, {f(ol("M0", "pismang_TK90"), 2)} ve {f(ol("M4S", "pismang_TK90"), 2)} birimdir ve sıralama iki düzende de korunmaktadır ({S_ref("sekil5_karar")}).'),
 ]),
 ('table', 'karar'),
 ('fig', 'sekil5_karar', 'Hizmet düzeyine göre TK modeline göre pişmanlık (orta sansür şiddeti). Sol panelde her hafta hedef stoka tamamlanmakta, sağ panelde kalan stok sonraki haftaya devretmektedir.'),

 ('h2', '4.7. Doğal veride sansür tanımına duyarlılık (AS6)'),
] + ([
 ('p', [
  O(f'Doğal veride bayraklı gün oranı tanıma göre {yz(min(_sr.values()))} ile {yz(max(_sr.values()))} arasında değişmektedir ({T_ref("dogal")}).'),
  O(f'M4 modelinin tahmin ettiği kayıp talep oranı en düşük {TAN[_ktmin]} tanımında {yz(_kt4[_ktmin])}, en yüksek {TAN[_ktmax]} tanımında {yz(_kt4[_ktmax])} olmuştur.'),
  O(f'Denetlenmiş dar tanımda (SR3) M4 modelinin kayıp talep oranı {yz(_kt4["CR3"])} düzeyindedir.'),
  O('Kayıp talep tahmini bayrak tanımına duyarlıdır ve örtük sıfır ile negatif stoklu günlerin işlenme biçimi tahmini doğrudan değiştirmektedir.'),
  O('İhtiyatlı SR2 tanımı stoku bir birimde kalan günleri de bayrakladığı için talebin tam gözlendiği günleri alt sınır sayan yanlış pozitif etiketler üretmekte ve deneydeki yanlış pozitif gürültüyle aynı yönde, yukarı yönlü bir kayma yaratmaktadır.'),
  O(f'Seri içi M3 modeli SR2 tanımında {yz(kt("CR2", "M3"), 0)} kayıp talep oranına ulaşmakta ve bu tanımda sınır çözümlerinin etkisi en yüksek düzeye çıkmaktadır.'),
  O(f'Test penceresindeki satışa göre M4 modeli SR3 tanımında talebi {yz(DN_["CR3"]["olcut"]["M4"]["t_yanlilik_satis"], 1, True)}, M0 modeli {yz(DN_["CR3"]["olcut"]["M0"]["t_yanlilik_satis"], 1, True)} fazla tahmin etmektedir, satış talebin alt sınırı olduğu için bu fark doğruluk ölçütü sayılmamaktadır.'),
  O('Bütün modellerin doğal veri sonuçları {EK:dogal_tam} içinde verilmiştir.'),
 ]),
] if _dog_var else [('p', [O('Doğal veri sonuçları hazırlanmaktadır.')])]) + [
 ('table', 'dogal'),

 ('h2', '4.8. Sağlamlık sınamaları'),
 ('p', [
  O(f'Test penceresinde en az yedi bilinen gün koşulu uygulandığında gözlem sayısı {n(S["eski_filtre_n"])} olmakta, M0 modelinin yanlılığı {yz(S["eski_filtre"]["M0"]["gk_yanlilik"])}, M4 modelinin yanlılığı {yz(S["eski_filtre"]["M4"]["gk_yanlilik"])} düzeyinde kalmaktadır ({EK_ref("filtre")}).'),
  O(f'Haftalık düzeyli M4D modeli toplam talepte {yz(ol("M4D", "gk_yanlilik"))} yanlılık vermiş, kıyas sapmasında ise M4 modelinden {f(-fk("kiyas_sapma", "M4D"), 3)} birim yüksek sapma üretmiştir ({EK_ref("m4z")}).'),
  O(f'Gerçek test talebine göre ise M4D modelinin ağırlıklı mutlak hatası ({f(_KH["M4D"]["test_wape"], 3)}) M4 modelinden ({f(_KH["M4"]["test_wape"], 3)}) düşüktür ve KS ölçütü durağan TB kıyası nedeniyle haftalık düzeyli sürümü cezalandırmaktadır.'),
  O(f'Serinin gerçek eğitim talebi ortalamasına dayanan havuzsuz TB0 kıyasında sıralama tersine dönmektedir: M0 {f(_KH["M0"]["ks_TB0"], 3)}, M2 {f(_KH["M2"]["ks_TB0"], 3)} ve M4 {f(_KH["M4"]["ks_TB0"], 3)} değerini almaktadır.'),
  O(f'TB0 kıyası test talebini {yz(ES["TB0_test_yanlilik"], 0, True)} fazla tahmin ettiği için bu sonuç seçilen kıyasın mimarisinin KS sıralamasını belirlediğini göstermekte ve H2b kararının TB kıyasına koşullu okunmasını gerektirmektedir.'),
  O(f'Hiyerarşi etkileri çıkarıldığında (M4H) kıyas sapması {f(ol("M4H", "kiyas_sapma"), 3)}, ortak değişkenler de çıkarıldığında (M4K) {f(ol("M4K", "kiyas_sapma"), 3)} değerine yükselmektedir.'),
  O(f'Mağaza ve alt kategori etkilerinin kaldırılması ϕ tahminini başlangıç noktasına göre {f(min(_ph), 1)} ile {f(max(_ph), 1)} arasına çıkarmaktadır, seri farkları havuzlama etkenleri yerine seri çarpanına yüklenmektedir.'),
  O(f'Ayar ızgaralarında M6 düzeltme katsayısı ve M2 pencere uzunluğu dört başlangıç noktasının tamamında kümenin alt ucunda ({f(ES["izgara"]["m6_alfa"][0], 2)} ve {ES["izgara"]["m2_w"][0]} gün) seçilmiştir, iki modelin sonuçları ızgaranın alt sınırına koşulludur.'),
  O('M4, M4S ve TB çözümleri dört başlangıç noktasının tamamında 200 yineleme sınırında durmuştur ve sınırın etkisi ilk başlangıç noktasında sınanmıştır.'),
 ] + ([
  O(f'Eğitim penceresi 56 güne indirildiğinde gözlem sayısı {n(_L["56"]["n_gozlem"])} olmakta, M4 modelinin yanlılığı {yz(_L["56"]["olcut"]["M4"]["gk_yanlilik"])}, M0 modelinin yanlılığı {yz(_L["56"]["olcut"]["M0"]["gk_yanlilik"])} düzeyinde kalmaktadır ({EK_ref("pencere")}).'),
  O('Kısa pencerede en az 28 geçerli gün ve en az bir birim satış koşulunu karşılayan seri sayısı azaldığı için gözlem sayısı ana düzenin altına inmektedir.'),
 ] if _L['56'] else []) + ([
  O(f'Başlangıç noktasından önceki bütün geçmiş kullanıldığında gözlem sayısı {n(_L["999"]["n_gozlem"])}, M4 modelinin yanlılığı {yz(_L["999"]["olcut"]["M4"]["gk_yanlilik"])}, M0 modelinin yanlılığı {yz(_L["999"]["olcut"]["M0"]["gk_yanlilik"])} olmuştur.'),
 ] if _L['999'] else []) + ([
  O(f'Sıfır şişkin M4Z modelinin kıyas sapması {f(ol("M4Z", "kiyas_sapma"), 3)}, yanlılığı {yz(ol("M4Z", "gk_yanlilik"))} olmuştur.'
    + (f' M4Z çözümleri dört başlangıç noktasının tamamında 100 yineleme sınırına ulaşmıştır ve bu sonuç sınıra koşulludur.' if _m4z_sinir() else '')),
 ] if 'M4Z' in OL else [])),

 ('h1', '5. Tartışma'),
 ('h2', '5.1. Sansür yanlılığı ve havuzlamanın payı'),
 ('p', [
  A('Satışı talep sayan modelin yanlılığının her şiddet düzeyinde kayıp talep payına eşit çıkması, tükenmeden doğan tahmin yanlılığının tükenme sıklığına bağlı olduğu yönündeki erken bulguyla uyumludur ve bağın bu veride birebir orantılı olduğunu eklemektedir.', 'wecker78',
    'The forecasting bias that results and the effect on the prediction error variance are explored and are seen to depend on the frequency of stockouts'),
  A('Saatlik etiketli veride yeniden sansürlenmiş talepteki yanlılığın −%8,1 düzeyinden −%1,3 düzeyine indirildiği çalışmayla karşılaştırıldığında, bu çalışmadaki iyileşme benzer büyüklüktedir.', 'yin26',
    'reduces re-censored demand bias from −8.1% to −1.3%'),
  O('Buradaki iyileşme saatlik etiket yerine gün sonu stok kaydından türetilen ve ölçüm anı denetlenen bir bayrakla elde edilmektedir.'),
  O('Yeniden sansürleme deneyinde bayrak tanım gereği hatasızdır ve sonuç gün sonu kaydının taşıyabileceği bilginin üst sınırını vermektedir, iki bilgi türünün aynı serilerde karşılaştırılması bu sınırın gerçek kayıtta ne kadar korunduğunu belirleyecektir.'),
 ]),
 ('p', [
  O(f'Kıyas sapmasındaki kazancın {yz(KA["mimari_pay"], 0)} kadarının havuzlu mimariden gelmesi ve maliyetteki kazancın sansürü yok sayan havuzlu modelde de görülmesi, seyrek perakende serisinde sansürden önce gelen sorunun bilgi azlığı olduğunu düşündürmektedir.'),
  A('Havuzlamanın başarısının verinin niteliklerine bağlı olduğu yönündeki bulgu, seçilen serilerin çoğunun eğitim penceresinde tek birim sattığı bu veride havuzlamanın sansür düzeltmesinin önkoşulu olmasıyla somutlaşmaktadır.', 'fildes22',
    'The data rich environment at lower product hierarchies makes data pooling an often appropriate strategy to improve forecasts, but success depends on the data characteristics and common factors influencing sales and potential demand.'),
  O('Seri içi sansürlü olabilirliğin seyrek seride sınır çözümlerine kayması bu yorumla uyumludur: sansürlü olabilirlik bilgi azlığını gidermemekte, havuzlamayla birleştiğinde işlemektedir.'),
  O('Kıyas sapmasının TB kıyasının mimarisine koşullu olması bu payın da koşullu okunmasını gerektirmektedir, havuzsuz bir kıyasa göre sansür düzeltmesinin göreli değeri başka bir büyüklükte çıkabilmektedir.'),
  O('Silme yaklaşımının toplam talepte rekabetçi kalması verinin yapısıyla açıklanabilmektedir: sansürlü günlerin büyük bölümünde talep sıfırdır ve bu günlerin silinmesi kalan günlerin ortalamasını gerçek düzeye yaklaştırmaktadır.'),
  O('Aynı yaklaşım sansürlü günü kendi düzeyindeki koşullu beklentiyle doldurmakta ve seriler arasında bilgi ödünç almamaktadır, seri düzeyindeki hata ve kıyas sapmasında M4 modelinin gerisinde kalması beklenen bir sonuçtur.'),
 ]),
 ('h2', '5.2. Stok etiketi ve veri kalitesi'),
 ('p', [
  A('Stok belirsizliğinin yok sayılmasının talep tahmininde sistematik aşağı yönlü yanlılık doğurduğu yönündeki kuramsal sonuç, bu çalışmada yanlış negatif etiket için geçerli çıkmaktadır.', 'mersereau15',
    'When the firm does not account for inventory uncertainty when estimating demand, we discover and characterize a systematic downward bias in demand estimation'),
  O('Yanlış pozitif etiket ters yönde bir kayma üretmektedir ve sansürsüz günlerin taban oranı yüksek olduğu için bu kayma yanlış negatif etiketin etkisinden büyüktür.'),
  O('Doğal veride stoku bir birimde kalan günleri de bayraklayan ihtiyatlı tanımın kayıp talebi katlarca büyütmesi, yanlış pozitif etiketin deney dışındaki olası karşılığıdır.'),
  O('Hata türü yanlılığın yönünü belirlediği için stok kaydı kalitesi talep tahmini açısından tek bir doğruluk oranıyla özetlenememektedir.'),
  A('Bir perakendecinin 37 mağazasındaki stok kayıtlarının üçte ikiye yakınının hatalı bulunduğu dikkate alındığında, deneydeki %20 hata düzeyi gerçekçi bir senaryo aralığının içinde kalmaktadır.', 'dehoratius08',
    'Examining nearly 370,000 inventory records from 37 stores of one retailer, we find 65% to be inaccurate.'),
  O('Denetimle kalibre edilen karışım modeli %20 hata düzeyinde yanlılığı yaklaşık yarıya indirmekte, daha düşük hata düzeylerinde ise aşağı yönde aşırı düzeltme yapmaktadır.'),
  O('Aşırı düzeltme hata payının satışlı ve satışsız bayraklı günlerde eşit varsayılmasından gelmektedir ve denetimin satış durumuna göre tabakalanması modelin doğrudan bir genişlemesidir.'),
  O('Kayıt hatasının yaygın olabildiği bir ortamda fiziksel sayım, stok kontrolünün yanında talep öğrenmenin de bilgi kaynağı olarak işlev görmektedir.'),
 ]),
 ('h2', '5.3. Tahmin doğruluğundan yenileme politikasına'),
 ('p', [
  A('Tahmin doğruluğu ile stok performansı arasındaki bağın zayıf kalabildiği yönündeki bulgu bu çalışmada da görülmektedir.', 'theodorou25',
    'this relationship may often be weak'),
  O('M4 modeli kıyas sapmasında M4S modelinden anlamlı düşük sapma verirken gerçek test talebine göre hata, SSOS ve maliyet ölçütlerinde M4S modeli öndedir.'),
  O('Bunun nedeni seçim kaynaklı düzey düşüşüdür: sansürü yok sayan model eğitim düzeyini eksik tahmin ettiği için test penceresindeki düşük düzeye rastlantısal olarak yaklaşmaktadır.'),
  O('Yanlı bir düzeyin maliyet ölçütünde ödüllenmesi, yenileme politikasının sınanmasında test dönemi kâhininin yanında tam bilgili eğitim kıyasının ve seçimden bağımsız bir değerlendirme kümesinin kullanılmasını gerektirmektedir.'),
  A('Pişmanlığın talep dağılımı bilindiğinde ulaşılan en iyi maliyete göre tanımlandığı çerçeveyle karşılaştırıldığında, bu çalışmadaki iki kıyas düzeni pişmanlığın kaynaklarını kısmen ayırabilmektedir.', 'besbes13',
    'We measure performance in terms of regret: the difference between the cumulative costs of a policy and the optimal cumulative costs with knowledge of the demand distribution.'),
  O('TB modeline kadar olan kısım sansürün, TB ile TK arasındaki kısım ise durağan olmayan talebin ve TK modelinin test sonuçlarıyla kurulmasından gelen ileriye bakışın bedelidir.'),
  O('M4S modelinin maliyetinin TB modelinin altında kalması, bu ayrıştırmanın bu test döneminde kesin bir alt sınıra dayanmadığını belirtmektedir.'),
 ]),
 ('h2', '5.4. Kuramsal çıkarımlar'),
 ('p', [
  O('Bilgi işleme görüşünde kararın kalitesi işlenen bilginin kalitesine bağlanmaktadır ve bulgular bu bağı dört halkalı ölçülebilir bir zincire çevirmektedir.'),
 ]),
 ('madde', [
  'Stok akışı özdeşliği, stok kaydının içsel kalitesini veriden sınayan bir denetim kuralı olarak çalışmaktadır.',
  'Sansür düzeltmesi, içsel olarak tutarlı fakat talep görevi için eksik olan satış kaydını bağlamsal olarak daha kaliteli bir talep bilgisine dönüştürmektedir ve dönüşümün büyük bölümü havuzlamadan gelmektedir.',
  'Bağlamsal kalitedeki artışın yenileme maliyetine aktarımı talebin durağanlığına ve değerlendirme kümesinin seçimine bağlı kalmaktadır.',
  'Bu çalışmadaki olabilirlik yapısında etiket hatası payı aynı veri akışından tahmin edilememektedir ve içsel veri kalitesi bilgisinin ayrı bir ölçüm sürecinden gelmesi gerekmektedir.',
 ]),
 ('h2', '5.5. Yönetsel çıkarımlar'),
 ('p', [
  O('Dijital iş yönetimi açısından bulgular dört uygulama önerisine dönüşmektedir.'),
 ]),
 ('madde', [
  'Satış ve stok kayıtları talep bilgisine dönüştürülmeden önce stok kaydının ölçüm anının basit bir stok akışı özdeşliğiyle veriden sınanması ve tükenme bayrağının bu sınamaya dayandırılması gerekmektedir.',
  'Seyrek ürünlerde kayıp talebin mağaza ve kategori bilgisinden ödünç alınarak tahmin edilmesi gerekmektedir, çünkü seri içi düzeltme yöntemleri seyrek ürünlerde kararsız sonuç vermektedir.',
  'Dönemsel fiziksel sayımların stok kontrolünün yanında talep tahmininin kalibrasyonu için de planlanması gerekmektedir, çünkü etiket hatasının büyüklüğü işlem kayıtlarından öğrenilememektedir ve sayımın satışlı ile satışsız bayraklı günleri ayrı kapsaması düzeltmenin doğruluğunu artırmaktadır.',
  'Sansür düzeltmesinin yenileme politikasına aktarılmasında düzey değişimini izleyen bir tahmin ve seçimden bağımsız bir değerlendirme kümesi kullanılması gerekmektedir, aksi durumda düzeltmenin maliyet kazancı havuzlamanın kazancından ayırt edilememektedir.',
 ]),
 ('h2', '5.6. Sınırlılıklar ve gelecek araştırmalar'),
 ('p', [
  O('Veri kimlik alanları kodlanmış tek bir perakende işletmesinden gelmektedir, veri sağlayıcısı kurum bilgisi vermemektedir ve bulgular başka zincirlere, kanallara ve ürün gruplarına doğrudan taşınamamaktadır.'),
  O('Yeniden sansürleme deneyi gerçek talebin bilindiği stoklu günler üzerine kurulmaktadır, deneyin sansür mekanizması gün içi tükenme zamanını taşımamakta ve gerçek tükenmelerin gün içindeki dağılımını yansıtamamaktadır.'),
  O('Sansürün stok düzeyi ve ortak değişkenler verildiğinde talepten bağımsız olduğu varsayımı, yenileme kararları talep şoklarına tepki verdiğinde yüksek talepli günlerin daha sık sansürlenmesine ve düzeltilmiş talebin aşağı yönlü kalmasına neden olabilmektedir, deney sansürü bu varsayımla ürettiği için varsayımı sınayamamaktadır.'),
  O('Veride saatlik zaman damgası ve fiziksel sayım bulunmadığı için etiket hatası benzetimle eklenmiş ve denetim örneklemi deney içinde kurulmuştur.'),
  O('Bilinen talep günleri doğal tükenme günlerini dışarıda bıraktığı için deneydeki talep dağılımının sağ kuyruğu kısalmaktadır ve deney, doğal veride en yüksek talepli günleri temsil etmekte zorlanabilmektedir.'),
  O(f'Doğal stoksuz dönemlerin {yz(ES["sure_havuzu"]["oran"], 0)} kadarı serinin son kayıt gününde sürdüğü için süre havuzunun dışında kalmıştır, havuz kısa tükenmelere ağırlık vermekte ve deneydeki sansür şiddeti doğal tükenmelerin süresini eksik temsil edebilmektedir.'),
  O('Yenileme gecikmesi takvim günüyle sayıldığı için doğal tükenme günleriyle örtüşen gecikmelerde yapay sansür süresi kısalmaktadır.'),
  O('M4R bayraksız günlerin gerçekte sansürlü olma olasılığını modele katmamakta, hata payını satış durumundan bağımsız varsaymakta ve yanlış negatif hatayı düzeltememektedir.'),
  O('Veri 328 günü kapsadığı için yıllık mevsimsel indeks tahmin edilememektedir ve modeller haftalık düzeyli sürüm dışında seri başına sabit bir düzey öğrenmektedir.'),
  O('Seri seçiminin test penceresindeki bilinen gün koşulu başlangıç noktasında bilinmemektedir ve karar katmanı test penceresindeki stoklu gün sayısını bilinen kabul etmektedir.'),
  O('Önyükleme havuzlu modellerin ortak parametrelerini yeniden tahmin etmediği için güven aralıkları dar kalabilmektedir.'),
  O('M4 çözümleri 200 yineleme sınırında durmuştur ve sınırın sonuçlara etkisi tek bir başlangıç noktasında sınanmıştır, M6 ve M2 modellerinin ayar değerleri ise ızgaranın alt sınırında seçilmiştir.'),
 ]),
 ('p', [
  O('Gelecek araştırmalar sansürlü olabilirliği durum uzayı modelleriyle birleştirerek düzey değişimini ve sansürü birlikte öğrenebilir.'),
  O('Gerçek fiziksel sayım verisiyle etiket hatası payının mağaza, kategori ve satış durumuna göre değişimi ölçülebilir ve sayım sıklığının talep öğrenmeye katkısı bir deney tasarımıyla sınanabilir.'),
  O('Saatlik satış zamanlaması bulunan veri setlerinde gün sonu bayrağıyla saatlik etiketin aynı seriler üzerinde karşılaştırılması günlük kayıtların taşıdığı bilginin sınırını belirleyecektir.'),
  O('Seçimden bağımsız bir değerlendirme kümesi ve stok durumunu da tahmin eden bir karar katmanı, sansür düzeltmesinin maliyet değerini havuzlamanın değerinden ayıracaktır.'),
 ]),

 ('h1', '6. Sonuç'),
 ('p', [
  O('Bu çalışma, perakendede stok tükenmesinin gizlediği talebin saatlik etiket ve fiziksel sayım olmadan, günlük satış ve gün sonu stok kayıtlarından öğrenilip öğrenilemeyeceğini sınamıştır.'),
  O('Yeniden sansürleme deneyinde yanıt, stok kaydının ölçüm anı veriden sınandığında ve kayıp talep mağaza ile kategori bilgisinden ödünç alınarak tahmin edildiğinde olumludur, doğal veride ise tahmin edilen kayıp talep bayrak tanımına bağlı kalmaktadır.'),
  O(f'Satışı talep sayan model, sansür şiddetine bağlı olarak gerçek talebin {yz(-gy("S_dusuk", "M0"), 1)} ile {yz(-gy("S_yuksek", "M0"), 1)} arasındaki bölümünü kaybetmektedir.'),
  O(f'Havuzlu sansürlü model bu yanlılığı bütün şiddet düzeylerinde {yz(_ust_sinir, 1)} sınırının altına indirmekte ve test penceresinde aynı mimariyle tam bilgiyle kurulan modele en yakın tahmini üretmektedir.'),
 ]),
 ('p', [
  O('Test tahminindeki kazancın büyük bölümü havuzlamadan, daha küçük fakat anlamlı bir bölümü sansür düzeltmesinden gelmektedir ve bu pay tam bilgili kıyasın mimarisine koşulludur.'),
 ] + ([O(f'Toplam talep yanlılığında havuzlu modelin {liste(_gy_ns)} karşısındaki üstünlüğü anlamlı bulunmamıştır ve kazanç seri düzeyindeki ve test penceresindeki ölçütlerde belirginleşmektedir.')] if _gy_ns else []) + [
  O('Kazanç, serinin sansürlü gün oranı arttıkça büyümektedir ve sansürlü günü sık olan seriler düzeltmenin asıl hedefidir.'),
  O('Stok etiketindeki hatanın türü düzeltilmiş talebin yönünü belirlemektedir, hatanın büyüklüğü ise bu çalışmadaki olabilirlik yapısında satış ve bayrak verisinden tahmin edilememekte ve fiziksel sayıma dayanan dışsal bir denetim gerektirmektedir.'),
 ]),
 ('p', [
  O(f'Yenileme politikasında havuzlu sansürlü model satışı talep sayan modele göre maliyeti {"anlamlı biçimde " if H5_m0 else ""}düşürmekte ve tam bilgiye göre oluşan kaybın {yz(1 - _kap, 0)} kadarını kapatmaktadır.'),
  O(('Sansürü yok sayan havuzlu model aynı kaybın tamamını kapattığı' if _kap_s <= 0 else f'Sansürü yok sayan havuzlu model aynı kaybın {yz(1 - _kap_s, 0)} kadarını kapattığı') + f' için maliyetteki kazanç havuzlamadan gelmektedir ve H5 {karar(H5)}.'),
  O('Test dönemindeki düşüş büyük ölçüde eğitimdeki rastlantısal satışla seçilen seyrek serilerin ortalamaya dönüşünden kaynaklanmaktadır ve düzeyi düşük tahmin eden modeli maliyette ödüllendirmektedir.'),
  O('Tahmin doğruluğundaki kazancın maliyete aktarılması, sansür düzeltmesinin düzey değişimini izleyen bir tahminle ve seçimden bağımsız bir değerlendirme kümesiyle birlikte uygulanmasına bağlıdır.'),
  O('Doğal veride tahmin edilen kayıp talep sansür bayrağının tanımına duyarlıdır ve bayrak tanımının raporlanması sansürlü talep çalışmalarında yeniden üretilebilirliğin koşuludur.'),
 ]),
 ('p', [
  O('Dijital iş yönetimi açısından çalışmanın sonucu, işletmenin kayıt sisteminde biriken verinin talep bilgisine dönüşmesinin üç adım gerektirdiğidir: stok kaydının denetimi, sansür bilgisinin havuzlu bir modelle işlenmesi ve stok kaydı kalitesinin fiziksel sayımla ölçülmesi.'),
  O('Kod, veri kartı, ara çıktılar ve ek tablolar açık depoda paylaşılmıştır ve bütün bulgular ham veriden tek bir komut dosyasıyla yeniden üretilebilmektedir.'),
 ]),
]
