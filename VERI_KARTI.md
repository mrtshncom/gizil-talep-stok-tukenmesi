# Veri seti kartı

## Kimlik

| Alan | Değer |
|---|---|
| Ad | Retail Transactions and Stocks Data |
| Sürüm | V1 |
| Yayımlayan depo | Mendeley Data |
| DOI | [10.17632/27x8mjm8k4.1](https://doi.org/10.17632/27x8mjm8k4.1) |
| Oluşturucu | Jimmy Smith (DataCite kaydındaki ad) |
| Atıf | Smith, J. (2026). *Retail Transactions and Stocks Data* (V1) [Veri seti]. Mendeley Data. https://doi.org/10.17632/27x8mjm8k4.1 |
| Lisans | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Depodaki kopya | `veri/Retail_Transactions_and_Stocks_Data.zip` (değiştirilmemiş özgün arşiv, SHA-256 `f65cb8ace7d2d7864986dde91ae658311cd334e5d6c742d3a9f9f8bfc9675480`) |
| Değişiklik | Arşiv ve içindeki dosyalar üzerinde hiçbir değişiklik yapılmamıştır. Bütün dönüşümler `analiz/` betiklerinde kod olarak tutulur. |

## Dosyalar ve bütünlük

| Dosya | Satır | SHA-256 |
|---|---:|---|
| `retail_sales_ml_apl.csv` | 125 751 | `da4763939baed1f46bfca7e893f9512a0294544494b1e794e5b8f2c59efbd2a1` |
| `retail_inventory_ml_apl.csv` | 284 755 | `c765678a26c2d024e8300b8f5b4a67cb2e2bde6e24213f202914557d000ce37d` |

Özetler `cikti/veri_bilgi.json` dosyasında yeniden hesaplanır. Satış dosyasındaki iade nedeni (`Reason of Return`) alanı bütün satırlarda boştur. Öteki alanlarda iki dosyada da eksik hücre yoktur.

## Kapsam

| Özellik | Değer |
|---|---|
| Dönem | 2025-06-01 ile 2026-04-24 (328 gün) |
| Mağaza | 40 (tek mağaza türü, tek satış kanalı) |
| Stok birimi | 2 326 |
| Ürün hiyerarşisi | 3 bölüm, 27 kategori, 51 alt kategori, 600 segment |
| Ürün türü | Ayakkabı ve giyim |
| Satış satırı | 125 751 (7 491 iade satırı, 2 sıfır adetli satır) |
| Stok aralık kaydı | 284 755 (22 701 açık uçlu, 13 869 sıfır, 1 380 negatif değerli) |
| Fiyat durumu (satış) | Tam fiyat 93 929, promosyon 23 651, birinci indirim 4 384, ikinci indirim 2 434, tasfiye 1 353 satır |

## Kayıt yapısı

Satış dosyası işlem satırı düzeyindedir: tarih, mağaza, stok birimi, adet, fiyat durumu ve iade göstergesi içerir. Stok dosyası her kaydı başlangıç ve bitiş tarihi arasında sabit kalan bir eldeki miktar olarak tutar. Kayıtlar gün düzeyine açılınca mağaza, stok birimi ve gün panelinde bir eldeki stok değeri oluşur (`analiz/veri_hazirla.py`).

## Alan sözlüğü

Satış dosyası (`retail_sales_ml_apl.csv`, 17 alan):

| Alan | Açıklama | Çalışmada kullanımı |
|---|---|---|
| `Transaction Date` | İşlem günü | Panelin gün ekseni |
| `Sales Type` | Fiyat durumu (Full Price, Promo, Markdown Tier 1, Markdown Tier 2, Clearance) | Betimleme ve sentetik veri sınaması |
| `Is Return` | İade satırı göstergesi (0 veya 1) | İade satırlarının sayımı |
| `Reason of Return` | İade nedeni | Bütün satırlarda boş |
| `Supplier` | Kodlanmış tedarikçi adı | Kimlik sınaması |
| `Product No` | Kodlanmış ürün numarası | Seri anahtarı |
| `Product Description` | Ürün açıklaması (kodlanmış ürün ve segment numarası ile ad) | Kimlik sınaması |
| `Product Division`, `Product Category`, `Product Subcategory`, `Product Segment` | Ürün hiyerarşisinin dört düzeyi | Betimleme ve havuzlama birimi |
| `Store` | Kodlanmış mağaza numarası | Seri anahtarı |
| `Sales Channel` | Satış kanalı (tek değer) | Betimleme |
| `Qty Sold` | Satılan adet (iadede negatif) | Günlük brüt satış ve iade |
| `Sales Amount` | Satış tutarı | Fiyat sonu ve fiyat ile maliyet oranı sınamaları |
| `Cogs` | Satılan malın maliyeti | Fiyat ile maliyet oranı sınaması |
| `Number of Transactions` | İşlem sayısı | Kullanılmaz |

Stok dosyası (`retail_inventory_ml_apl.csv`, 18 alan):

| Alan | Açıklama | Çalışmada kullanımı |
|---|---|---|
| `Start Date`, `End Date` | Kaydın geçerli olduğu ilk ve son gün (son gün boş olabilir) | Kaydın güne açılması |
| `Stock Status` | Stok fiyat durumu | Betimleme |
| `Supplier`, `Product No`, `Product Description` | Satış dosyasındaki tanımlarla aynı | Seri anahtarı ve kimlik sınaması |
| `Product Division`, `Product Category`, `Product Subcategory`, `Product Segment` | Ürün hiyerarşisi | Satış dosyasıyla eşleştirme |
| `Store`, `Store Type`, `Sales Channel` | Mağaza, mağaza türü ve kanal (son ikisi tek değer) | Seri anahtarı |
| `Qty on hand` | Eldeki miktar | Sansür bayrağı ve stok akışı denetimi |
| `Stocks Selling Amount`, `Cost of Stocks` | Eldeki stokun satış ve maliyet değeri | Kullanılmaz |
| `Stock Unit Selling Price`, `Stock Unit Cost Price` | Birim satış fiyatı ve birim maliyet | Birim satış fiyatı panelde günlük fiyat olarak tutulur, birim maliyet kullanılmaz |

## Ölçüm anı ve sansür bayrağı

Veri setinin açıklaması stok kaydının gün içindeki ölçüm anını belirtmez. Ölçüm anı stok akışı özdeşliğiyle veriden sınanmıştır (`analiz/denetim.py`, `analiz/ek_denetim.py`):

* Ardışık iki günde kaydı bulunan ve o günün net satışı sıfırdan farklı olan 77 131 günün %97,3'ünde stok düşüşü aynı günün net satışına eşittir. Aynı paydada önceki günün net satışıyla eşleşme %4,9, iki koşulun birlikte sağlanması %3,1 düzeyindedir.
* Satış olmayan günlerin %99,6'sında stok değişmez.
* Kaydın kesildiği günlere sıfır stok atayan örtük sıfır kuralından sonra 107 425 satış gününde eşleşme oranı %97,5'tir.

Bu sonuçlar stok kaydını gün sonu miktarı olarak okumayı destekler. Sansür bayrağının beş tanımı (SR1 ile SR5) `analiz/denetim.py` ve `analiz/ek_denetim.py` içinde kurulur ve `analiz/deney.py` içinde kullanılır. Kodda, JSON anahtarlarında ve `D_CR*` senaryo adlarında aynı tanımlar CR1 ile CR5 adını taşır.

## Kalite bayrakları

| Bayrak | Sayı | Not |
|---|---:|---|
| Etkin seri-gün | 9 704 922 seri-gün | 60 968 seri |
| Örtük sıfır | 337 938 seri-gün | 38 267 son kayıt sonrası, 299 671 iç boşluk |
| Negatif stok | 53 166 seri-gün | 977 seri |
| Satışla açıklanmayan son kayıt düşüşü | 10 350 olay | Her olay bir serinin son kaydındadır. Olay sayısı SR1 sansürlü gün sayısının (1 185 667) %0,87'si kadardır. |
| İade bulunan seri-gün | 7 249 seri-gün | etkin seri-günlerin %0,07'si |

## Sentetik veri sınaması

Veri setinin sentetik üretilip üretilmediği kullanılmadan önce sınanmıştır (`analiz/sentetik_test.py`, çıktı `cikti/sentetik_test.json`). Sınama altı gösterge kümesine dayanır:

1. **İade ile satış bağı.** 7 491 iade satırının %90,6'sında aynı mağaza ve stok biriminin daha önceki bir satışı vardır. Medyan gecikme 2 gündür ve iadelerin %83,4'ü 30 gün içinde gelir. İade tarihleri rastgele karıştırıldığında (200 permütasyon) bu pay ortalama %61,6, en yüksek %62,8 olur ve medyan gecikme 40,5 güne çıkar (p = 0,005).
2. **Takvim izi.** En yoğun gün 2025-12-24'tür ve aynı haftanın günü ortalamasının 7,67 katıdır. 2025-11-28 (Kara Cuma) 2,61 kat, 2026-02-14 2,06 kat, ağustos sonu okula dönüş haftaları ve aralık ayı (20 110 birim) yüksek satış dönemleridir. Cumartesi satışı pazartesi satışının 2,51 katıdır.
3. **Fiyat sonları.** Fiyatların %33,7'si .99, %61,9'u .00 ile biter.
4. **Dağılım.** Satış günlerinin %3,8'inde birden fazla birim satılır, stok birimlerinin en yoğun %10'u birimlerin %35,5'ini taşır, stok kayıtlarının %35,5'i 1 birimdir ve 1 380 kayıt negatiftir.
5. **Operasyon izi.** Stok kayıtlarındaki 35 482 stok girişi haftanın günlerine eşit dağılmaz (χ² = 1 376). Mağaza başına en yoğun giriş gününün payının medyanı %19,8'dir. Girişler mağaza içinde günlere rastgele dağıtıldığında bu medyan en çok %16,3 olur (p = 0,005). Tam fiyatlı satışlarda fiyatın maliyete oranının medyanı 1,977'dir ve satışların %41,2'sinde oran 2 ± 0,05 aralığındadır.
6. **Kimlik izi.** Ürün açıklamasındaki ürün numarası kayıttaki ürün numarasıyla hiç eşleşmez, segment kodu ise her zaman eşleşir. Tedarikçi ve kanal adları (örnek: "Channel Alpha") sınırlı bir sözcük dağarcığından gelir. Bu iki iz takma adlandırmaya (anonimleştirmeye) uyar.

Takvim, operasyon, iade ve fiyat izleri ile iki bağımsız tablo arasındaki %97,3'lük stok akışı tutarlılığı birlikte okunduğunda veri, takma adlandırılmış gerçek işlem kaydı niteliği taşır. Sentetik üretime işaret eden bir iz bulunmamıştır.

## Bilinen sınırlar

* Tek perakendeci ve 328 gün: yıllık mevsimsellik tahmin edilemez.
* Gün içi satış zamanı ve fiziksel raf sayımı yoktur.
* Sipariş ve tedarik süresi alanları yoktur. Maliyet alanları (`Cogs`, `Cost of Stocks`, `Stock Unit Cost Price`) bulunur. Satış dosyasındaki `Cogs` alanı fiyat ile maliyet oranı sınamasında kullanılmıştır.
* Kişisel veri içermez.

## Kullanım amacı

Çalışmada veri, gizil talep tahmin yöntemlerinin karşılaştırılmasında ve stok kaydının sansür bilgisi olarak denetlenmesinde kullanılmıştır.
