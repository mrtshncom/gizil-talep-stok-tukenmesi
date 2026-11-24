# -*- coding: utf-8 -*-
"""Ana metin ve ek tabloları. Her fonksiyon (başlık, sütunlar, satırlar, not) döndürür.
Hücrelerdeki {R:anahtar} ifadesi kaynak numarasına çevrilir. Sayılar analiz çıktılarından okunur."""
import os, json
from sayilar import *

def _tarih(s): return f'{s[8:10]}.{s[5:7]}.{s[:4]}'
AD = {'M0': 'Satışı talep sayan', 'M1': 'Silme', 'M2': 'Kayan profil ataması', 'M3': 'Seri içi sansürlü Poisson',
      'M5': 'Kaplan-Meier', 'M6': 'Sansürlü üstel düzeltme', 'M4': 'Havuzlu sansürlü (seçim koşullu)',
      'M4R': 'M4, denetimli etiket hatası', 'M4Z': 'M4, sıfır şişkin', 'M4D': 'M4, haftalık düzey', 'M4S': 'M4, sansürü yok sayan',
      'M4H': 'M4, hiyerarşisiz', 'M4K': 'M4, hiyerarşisiz ve ortak değişkensiz', 'TB': 'Tam bilgili eğitim kıyası',
      'TK': 'Test kâhini'}

# ------------------------------------------------------------------ ana metin, sonuçtan bağımsız
def t_literatur():
    sat = [
        ['{R:conrad76}', 'T1', 'Analitik, gazete satıcısı', 'Satış ile talep farkı', 'Doğru kabul', 'Satıştan talebe geçiş sorunu'],
        ['{R:wecker78}', 'T1', 'Analitik', 'Tükenme sıklığı', 'Doğru kabul', 'Yanlılığın belirleyicileri (H1)'],
        ['{R:nahmias94}', 'T1', 'Benzetim, normal talep', 'Talebin satıştan büyük olduğu bilinir', 'Doğru kabul', 'Sansürlü olabilirlik'],
        ['{R:agrawal96}', 'T1', 'Perakende zinciri, negatif binom', 'Kayıp satış gözlenemez', 'Doğru kabul', 'Yapay kesme ile doğrulama'],
        ['{R:anupindi98}', 'T1', 'Otomat verisi', 'Tükenme anı eksik veri', 'Doğru kabul', 'Satış hızındaki yanlılık'],
        ['{R:conlon13}', 'T1', 'Otomat verisi, dört saatlik izleme', 'Bulunurluk ölçülür', 'Doğru kabul', 'Bulunurluk yok sayılınca yanlılık'],
        ['{R:musalem10}', 'T1', 'Mağaza verisi, yapısal model', 'Kısmi bulunurluk', 'Doğru kabul', 'Seyrek üründe kayıp satış'],
        ['{R:wang25}', 'T1', 'Saatlik etiketli ön baskı veri', 'Saatlik tükenme etiketi', 'Doğru kabul', 'Etiketli veriye bağımlılık'],
        ['{R:yin26}', 'T1, T3', 'Etiketli veri, yeniden sansürleme', 'Tükenme işareti', 'Doğru kabul', 'Alt sınır yaklaşımı'],
        ['{R:trapero24}', 'T1, T3', 'Benzetim ve vaka, Tobit Kalman', 'Kayıp satış politikası', 'Doğru kabul', 'Sansürlü tahmin boşluğu'],
        ['{R:besbes13}', 'T1, T3', 'Kuramsal pişmanlık sınırları', 'Kayıp satış göstergesi', 'Doğru kabul', 'Gösterge bilgisinin değeri'],
        ['{R:jain15}', 'T1, T3', 'Bayesçi çok dönemli model', 'Satış zamanlaması', 'Doğru kabul', 'Tükenme zamanı bilgisi'],
        ['{R:huh11}', 'T1, T3', 'Parametresiz uyarlanabilir politika', 'Sansürlü satış', 'Doğru kabul', 'Kaplan-Meier tabanlı politika'],
        ['{R:sachs14}', 'T1, T3', 'Perakende verisi, veri güdümlü model', 'Saatlik zamanlama', 'Doğru kabul', 'Yüksek sansürde başarı'],
        ['{R:dehoratius08}', 'T2', f'{n(370000)} kayıt, 37 mağaza', 'Kapsam dışı', 'Kayıtların %65’i hatalı', 'Kayıt hatasının yaygınlığı'],
        ['{R:kang05}', 'T2, T3', 'Analitik ve benzetim', 'Görünmeyen tükenme', 'Stok kaybıyla bozulur', 'Kayıt hatası ile tükenme bağı'],
        ['{R:shabani21}', 'T2', '81 mağaza, moda perakendesi, veri zarflama', 'Kayıt hatası kaynaklı tükenme', 'Kayıt-fiziksel stok uyumsuzluğu', 'Kayıt hatasının tanımı'],
        ['{R:mersereau15}', 'T1, T2', 'Analitik ve sayısal', 'Sansürlü satış', 'Belirsiz', 'Aşağı yönlü yanlılık (H4)'],
        ['{R:chehrazi25}', 'T2, T3', 'Sürekli zamanlı Bayesçi stok modeli', 'Raf stoku gözlenemez', 'İşlem hatası ve gözlenemeyen kayıp', 'Raf stoku belirsizliği ve yenileme eşiği'],
        ['{R:croston72}', 'T4', 'Analitik', 'Kapsam dışı', 'Kapsam dışı', 'Aralıklı talepte ayrık tahmin'],
        ['{R:syntetos05}', 'T4', 'Sınıflandırma kuralları', 'Kapsam dışı', 'Kapsam dışı', 'Aralıklılık ve değişkenlik (H3)'],
        ['{R:snyder12}', 'T4', 'Yavaş dönen stok, dağılım karşılaştırması', 'Kapsam dışı', 'Kapsam dışı', 'Esnek sayım dağılımı'],
        ['{R:theodorou25}', 'T3', 'M5 verisi, benzetim', 'Kapsam dışı', 'Doğru kabul', 'Doğruluk ile maliyet bağı (H5)'],
        ['Bu çalışma', 'T1–T4', 'Açık perakende verisi, yeniden sansürleme', 'Gün sonu kaydından türetilir ve sınanır', 'Etiket hatası sınanır', 'İki literatürün kesişimi'],
    ]
    return ('Sansürlü talep ve stok kaydı literatürünün temalara göre sentezi',
            ['Kaynak', 'Tema', 'Veri ve tasarım', 'Sansür bilgisi', 'Stok kaydı', 'Bu çalışmadaki yeri'], sat,
            'T1: sansürlü talep tahmini, T2: stok kaydı hatası, T3: tahminden yenileme kararına geçiş, T4: aralıklı talep. '
            'Temalar tarama öncesinde araştırma sorularından belirlenmiştir. Bir kaynak, birden fazla temanın sorusuna veri, yöntem ya da bulgu düzeyinde doğrudan katkı verdiğinde her birine atanmıştır. '
            'Her kaynak için tema, veri ve tasarım, sansür bilgisi, stok kaydı ve bu çalışmadaki yeri aynı formla kaydedilmiştir. Hücreler kaynakların yayımlanmış özet metinlerinden derlenmiştir ve özet metninde karşılığı bulunmayan nitelik için kapsam dışı yazılmıştır. Tabloya, taramada atıf alan ve temalardan en az birine veri, yöntem ya da bulgu düzeyinde doğrudan katkı veren kaynaklar alınmıştır. Kaynaklar metindeki numara sırasıyla verilmiştir.')

def t_sansur_tanim():
    sat = []
    tan = [('SR1', 'Geniş', 'Gün sonu stoku ≤ 0', 'Etkin pencerenin bütün günleri', DN['CR1']),
           ('SR2', 'İhtiyatlı', 'Gün sonu stoku ≤ 1', 'Etkin pencerenin bütün günleri', DN['CR2']),
           ('SR3', 'Dar', 'Açık kayıtlı gün sonu stoku = 0', 'Örtük sıfır ve negatif stoklu günler dışarıda', DN['CR3']),
           ('SR4', 'Negatifsiz geniş', 'SR1 bayrağı', 'Negatif stoklu günler dışarıda', EK['CR4']),
           ('SR5', 'Dar bayrak, tam küme', 'SR3 bayrağı', 'Örtük sıfır ve negatif stoklu günler sansürsüz sayılır', EK['CR5'])]
    for kod, ad, kural, kume, d in tan:
        sat.append([f'{kod} {ad}', kural, kume, n(d['gun']), yz(d['oran']), yz(d['birim_sansurlu'])])
    return ('Sansür bayrağı tanımları ve etkin penceredeki sıklıkları',
            ['Tanım', 'Bayrak kuralı', 'Analiz kümesi', 'Seri-gün', 'Sansürlü gün', 'Sansürlü günlerdeki satış birimi'], sat,
            'Oranlar etkin pencerenin bütünü üzerinden hesaplanmıştır. Doğal veri analizi her tanımla ayrı yürütülmüştür.')

# ------------------------------------------------------------------ ek tablolar, sonuçtan bağımsız
def t_veri_karti():
    kal = DN['kalite']; sha = V['sha256']
    st = V['satis_turu']
    sat = [
        ['Kaynak', 'Smith (2026), Mendeley Data, V1, doi:10.17632/27x8mjm8k4.1 {R:veri}'],
        ['Lisans', 'CC BY 4.0'],
        ['Veri sağlayıcısının tanımı', 'Dört düzeyli ürün hiyerarşili bir perakende işletmesinden tabakalı örneklem'],
        ['Satış dosyası (SHA-256 ilk 16 karakter)', f'retail_sales_ml_apl.csv ({sha["retail_sales_ml_apl.csv"][:16]})'],
        ['Stok dosyası (SHA-256 ilk 16 karakter)', f'retail_inventory_ml_apl.csv ({sha["retail_inventory_ml_apl.csv"][:16]})'],
        ['Satış satırı, iade satırı', f'{n(V["satis_satir"])}, {n(V["iade_satir"])}'],
        ['Stok aralık kaydı, açık uçlu kayıt', f'{n(V["stok_satir"])}, {n(V["stok_acik_uclu"])}'],
        ['Negatif ve sıfır stok kaydı', f'{n(V["stok_negatif_kayit"])} ve {n(V["stok_sifir_kayit"])}'],
        ['Dönem', f'{_tarih(V["tarih_bas"])}–{_tarih(V["tarih_son"])} ({n(V["T"])} gün)'],
        ['Mağaza, stok birimi', f'{n(V["magaza"])}, {n(V["sku"])}'],
        ['Bölüm, kategori, alt kategori, segment', f'{n(V["bolum"])}, {n(V["kategori"])}, {n(V["altkategori"])}, {n(V["segment"])}'],
        ['Satış kanalı ve mağaza türü', 'Tek kanal, tek mağaza türü'],
        ['Satış türü (satır)', f'Tam fiyat {n(st["Full Price"])}, promosyon {n(st["Promo"])}, indirim {n(st["Markdown Tier 1"] + st["Markdown Tier 2"])}, tasfiye {n(st["Clearance"])}'],
        ['İade nedeni alanı', f'Bütün satırlarda boş ({n(V["iade_neden_bos"])} satır)'],
        ['Öteki alanlarda eksik hücre (satış, stok)', f'{n(V["eksik_hucre_satis"])}, {n(V["eksik_hucre_stok"])}'],
        ['Mağaza-ürün serisi (panel)', n(V['P'])],
        ['Etkin pencere: seri, seri-gün, satış birimi', f'{n(kal["etkin_seri"])}, {n(kal["etkin_gun"])}, {n(kal["etkin_birim"])}'],
        ['Örtük sıfır seri-gün (iç, son)', f'{n(EK["ortuk"])} ({n(EK["ortuk_ic"])}, {n(EK["ortuk_terminal"])})'],
        ['Negatif stoklu seri-gün (seri)', f'{n(kal["negatif_stok_gun"])} ({n(kal["negatif_stok_seri"])})'],
        ['Stok düşüşü = aynı gün net satış', f'{yz(EK["ayni_gun_esles_ayni_payda"])} ({n(EK["payda_ayni_gun"])} gün)'],
        ['Stok düşüşü = önceki gün net satış', f'{yz(EK["onceki_gun_esles_ayni_payda"])} (aynı payda)'],
        ['Örtük sıfır kuralı sonrası eşleşme', f'{yz(DN["anlam_ortuk_sifir"]["tam_eslesme"])} ({n(DN["anlam_ortuk_sifir"]["satis_gunu_n"])} gün)'],
        ['İade içeren seri-gün, iadenin satış birimine oranı', f'{n(EK["iade_seri_gun"])}, {yz(EK["iade_birim_orani"])}'],
        ['Kullanım amacı', 'Gizil talep tahmin yöntemlerinin yeniden sansürleme ile sınanması'],
        ['Kullanım sınırı', 'Kimlik alanları kodlanmıştır, saatlik zaman damgası ve fiziksel sayım bulunmamaktadır'],
    ]
    return ('Veri kartının özeti', ['Alan', 'Değer'], sat,
            'Tam SHA-256 değerleri ve alan tanımları açık depodaki veri kartında verilmiştir.')

def t_sentetik():
    ib = ST['iade_satis_bagi']; tk = ST['takvim']; fy = ST['fiyat']; dg = ST['dagilim']; km = ST['kimlik']
    sat = [
        ['Kimlik', 'Ürün adı ile ürün numarası eşleşmesi', yz(km['aciklama_urun_no_eslesme']), 'Adlar numaradan türetilmemiştir'],
        ['Kimlik', 'Ürün adı ile segment eşleşmesi', yz(km['aciklama_segment_eslesme']), 'Adlar segment düzeyinde kodlanmıştır'],
        ['Kimlik', 'Ürün adlarını oluşturan farklı sözcük', n(km['ad_sozcuk_sayisi']), 'Kodlanmış sözlük'],
        ['İade', 'Önceki satışı bulunan iade payı', yz(ib['onceki_satis_payi']), f'Plasebo ortalaması {yz(ib["plasebo_onceki_satis_payi_ort"])}, en büyüğü {yz(ib["plasebo_onceki_satis_payi_max"])}'],
        ['İade', 'İade gecikmesi medyanı (gün)', f(ib['gecikme_medyan_gun'], 0), f'Plasebo ortalaması {f(ib["plasebo_gecikme_medyan_ort"], 1)}'],
        ['İade', '30 gün içinde iade payı', yz(ib['gecikme_30_gun_payi']), f'Plasebo ortalaması {yz(ib["plasebo_gecikme30_ort"])}, {p(ib["p_degeri"])}'],
        ['Takvim', 'Cumartesi / pazartesi satış oranı', f(tk['cumartesi_pazartesi_orani']), 'Haftalık alışveriş döngüsü'],
        ['Takvim', '24.12.2025 / aynı gün ortalaması', f(tk['y_2025_12_24_ayni_gun_orani']), 'Yılbaşı öncesi sıçrama'],
        ['Takvim', '28.11.2025 / aynı gün ortalaması', f(tk['bf_2025_11_28_ayni_gun_orani']), 'Kasım indirim günü'],
        ['Takvim', '14.02.2026 / aynı gün ortalaması', f(tk['sevgililer_2026_02_14_ayni_gun_orani']), 'Sevgililer Günü'],
        ['Fiyat', ',00 ve ,99 ile biten fiyat payı', f'{yz(fy["sonu_00_payi"])} ve {yz(fy["sonu_99_payi"])}', 'Psikolojik fiyatlama'],
        ['Dağılım', 'En çok satan %10 stok biriminin birim payı', yz(dg['ilk_yuzde10_sku_birim_payi']), 'Çarpık satış dağılımı'],
        ['Dağılım', 'Birden fazla birim satılan gün payı', yz(dg['gunluk_birden_fazla_payi']), 'Seyrek, düşük hacimli talep'],
        ['Operasyon', 'Stok girişlerinin gün dağılımı (χ²)', f(ST['operasyon']['ki_kare'], 0), p(ST['operasyon']['ki_kare_p'])],
        ['Operasyon', 'Mağaza başına en yoğun giriş günü payı (medyan)', yz(ST['operasyon']['magaza_en_yogun_gun_payi_medyan']), f'Plasebo en büyüğü {yz(ST["operasyon"]["plasebo_medyan_max"])}, {p(ST["operasyon"]["plasebo_p"])}'],
        ['Operasyon', 'Tam fiyat / maliyet oranı (medyan)', f(ST['operasyon']['tam_fiyat_maliyet_medyan']), f'Satışların {yz(ST["operasyon"]["tam_fiyat_2_yakini"])} kadarı 2 ± 0,05 aralığında'],
        ['Tutarlılık', 'Stok düşüşü = aynı gün net satış', yz(EK['ayni_gun_esles_ayni_payda']), 'Tablolar arası işlem bağı'],
    ]
    return ('Sentetik veri sınamasının sonuçları', ['Sınama', 'Gösterge', 'Değer', 'Kıyas veya yorum'], sat,
            f'Plasebo sınamasında iade tarihleri seri içinde rastgele kaydırılmış ve {n(ib["plasebo_sayisi"])} tekrar yapılmıştır. '
            'Olasılık değeri, plasebo payının gözlenen payı aştığı tekrar sayısından hesaplanmıştır. Operasyon sınamasının plasebosunda her mağazanın stok girişleri haftanın günlerine rastgele dağıtılmıştır.')

def t_tarama():
    tk = json.load(open(os.path.join(os.environ.get('LIT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'literatur')), 'tarama_kaydi.json')))
    sat = []
    for s in tk['sorgular']:
        sat.append([s['sorgu'], n(s['toplam']), n(s['incelenen']), n(s.get('tur', {}).get('journal-article', 0)),
                    ', '.join('{R:' + k + '}' for k in s['atif_yapilan_eslesme']) or '–'])
    _yaz = {'pandas', 'numpy', 'scipy', 'statsmodels', 'matplotlib', 'veri'}
    _dis = [k for k in tk['sorgular_disi_atif'] if k not in _yaz]
    return ('Literatür taraması: sorgular ve kayıt sayıları', ['Sorgu', 'Crossref eşleşme sayısı', 'İncelenen', 'Dergi makalesi', 'Atıf yapılan eşleşme'], sat,
            f'Tarama {_tarih(tk["tarih"])} tarihinde Crossref arayüzünde, yayım tarihi 31.10.2026 ve öncesiyle sınırlanarak yapılmıştır. '
            'Her sorguda ilgi sırasına göre ilk 50 kayıt başlık ve özet düzeyinde incelenmiştir. '
            'Dahil etme ölçütleri hakemli yayın olması, perakende veya stok yönetiminde sansürlü talep, kayıp satış, stok kaydı hatası ya da karar değeri konularından birini incelemesi ve özet metnine erişilebilmesidir. '
            f'Sorgulardan {len(tk["sorgularda_bulunan_atif"])} kaynak atıf almış, {len(_dis)} kaynak bu kaynakların kaynakçalarından geriye doğru atıf izlemeyle ve yöntem kaynaklarından, '
            f'{len(_yaz)} kaynak ise veri ve yazılım kaydı olarak eklenmiştir.')

def t_yazilim():
    sat = [['Python', '3.13.18', 'Çalışma ortamı'], ['pandas', '3.0.5', 'Veri işleme {R:pandas}'], ['NumPy', '2.5.3', 'Dizi hesapları {R:numpy}'],
           ['SciPy', '1.18.1', 'En iyileme ve özel fonksiyonlar {R:scipy}'], ['statsmodels', '0.15.0', 'Kümelenmiş regresyon {R:statsmodels}'],
           ['Matplotlib', '3.11.2', 'Şekiller {R:matplotlib}']]
    return ('Yazılım sürümleri', ['Yazılım', 'Sürüm', 'Kullanım'], sat, 'Sürümler analizlerin yürütüldüğü ortamdan alınmıştır.')

def t_modeller():
    sat = [['M0', AD['M0'], 'Kullanılmaz', 'Yok'], ['M1', AD['M1'], 'Sansürlü gün silinir', 'Yok'],
           ['M2', AD['M2'], 'Koşullu atama', 'Yok'], ['M3', AD['M3'], 'Seri içi olabilirlik', 'Yok'],
           ['M5', AD['M5'], 'Çarpım limit tahmini', 'Yok'], ['M6', AD['M6'], 'Koşullu güncelleme', 'Ortak düzeltme katsayısı'],
           ['M4', AD['M4'], 'Havuzlu olabilirlik', 'Mağaza, alt kategori, ortak değişken'],
           ['M4R', AD['M4R'], 'Denetimden alınan hata payı $a$', 'M4 ile aynı'], ['M4Z', AD['M4Z'], 'Havuzlu olabilirlik', 'M4 ve bölüm başına sıfır olasılığı'],
           ['M4D', AD['M4D'], 'Havuzlu olabilirlik', 'M4 ve hafta etkileri'], ['M4S', AD['M4S'], 'Kullanılmaz', 'M4 ile aynı'],
           ['M4H', AD['M4H'], 'Havuzlu olabilirlik', 'Gün, fiyat durumu, ürün yaşı'], ['M4K', AD['M4K'], 'Havuzlu olabilirlik', 'Seri önseli'],
           ['TB', AD['TB'], 'Gerçek eğitim talebi', 'M4 ile aynı'], ['TK', AD['TK'], 'Gerçek test talebi', 'M4 ile aynı']]
    return ('Karşılaştırılan modeller', ['Kod', 'Model', 'Sansür bilgisi', 'Havuzlama'], sat,
            'TB ve TK yeniden sansürleme deneyine özgü kıyas modelleridir ve sansürlü veriyle kurulamazlar.')

TUM = {'literatur': t_literatur, 'sansur_tanim': t_sansur_tanim, 'veri_karti': t_veri_karti, 'sentetik': t_sentetik,
       'tarama': t_tarama, 'yazilim': t_yazilim, 'modeller': t_modeller}

# sonuca bağlı tablolar ayrı modülde tanımlanır ve buraya eklenir
try:
    from tablolar_sonuc import TUM as _TS
    TUM.update(_TS)
except ImportError:
    pass
