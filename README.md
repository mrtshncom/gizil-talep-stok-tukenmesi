# Stok tükenmesinin gizlediği perakende talebinin tahmini: yeniden üretim paketi

Bu depo, "Stok Tükenmesinin Gizlediği Perakende Talebinin Günlük Satış ve Stok Kayıtlarından Tahmini" başlıklı makalenin
bütün analizlerini ham veriden başlayarak yeniden üretmek için gereken kodu, veri kartını, ara çıktıları ve ek tabloları içerir.

*Estimating Retail Demand Hidden by Stockouts from Daily Sales and Stock Records: replication package. All code, the
dataset card, intermediate outputs and appendix tables are provided. Text is in Turkish.*

## Veri

- Kaynak: Smith, J. (2026). *Retail Transactions and Stocks Data* (V1). Mendeley Data. https://doi.org/10.17632/27x8mjm8k4.1
- Lisans: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Ham zip dosyası `veri/` klasöründe değiştirilmeden saklanmıştır ve sağlayıcının CC BY 4.0 lisansına tabidir.
- Veri kartı: [`VERI_KARTI.md`](VERI_KARTI.md) (kimlik, SHA-256 özet değerleri, kapsam, alan sözlüğü, ölçüm anı denetimi, kalite bayrakları, sentetik veri sınaması, kullanım sınırları).

## Klasörler

| Klasör | İçerik |
|---|---|
| `analiz/` | Bütün betikler. Makaledeki her sayı `cikti/*.json` dosyalarından otomatik okunur. |
| `cikti/` | `veri_bilgi.json`, `denetim.json`, `ek_denetim.json`, `sentetik_test.json`, `sonuclar.json`, `ek_sinama.json`, `kanit_raporu.csv`, panel dosyaları (`panel.npz`, `panel_ham.npz`, `seriler.csv`, `bosluk_sureleri.npy`), `sekil/` (600 dpi, siyah beyaz), `log/` (her deney koşusunun kaydı). |
| `ekler/` | Ek tablolar (`Ek_Tablolar.docx` ve her tablo için CSV). |
| `literatur/` | Atıf yapılan her DOI için Crossref veya DataCite kaydı (`cr/`), atıf yapılan DOI listesi (`dois.txt`), kanıt pasajı aranan kaynakların özet metninin alındığı adres (`ozet/*.kaynak`), literatür tarama kaydı (`tarama_kaydi.json`). Yayıncı hakları nedeniyle özet metinlerinin kendisi depoya konmamıştır. |
| `veri/` | Ham veri zip dosyası. |

## Betikler

| Betik | Görev |
|---|---|
| `literatur_tarama.py` | Crossref sorgularıyla literatür taramasını yapar ve `literatur/tarama_kaydi.json` dosyasını yazar (ağ bağlantısı gerektirir). |
| `kaynaklar.py` | Kaynak anahtarı ile DOI eşlemesi, `literatur/cr/` kayıtlarından APA kaynakça satırı. `LIT` ortam değişkeni literatür klasörünü değiştirir. |
| `veri_hazirla.py` | Ham dosyalardan mağaza × ürün × gün panelini kurar. |
| `denetim.py` | Stok kaydının ölçüm anını stok akışı özdeşliğiyle sınar, örtük sıfır kuralını ve SR1–SR3 sansür tanımlarını uygular. |
| `ek_denetim.py` | Aynı paydada eşleşme oranları, iade payları, iç boşluklar, SR4 ve SR5 tanımları. |
| `sentetik_test.py` | Kimlik, iade-satış bağı (plasebo sınaması), takvim, fiyat, dağılım ve operasyon (stok girişi günleri, fiyat/maliyet oranı) sınamaları. |
| `modeller.py` | M0–M6 kıyas modelleri ve M4 ailesi (seçim koşullu marjinal olabilirlik, sınırlı bellekli BFGS, analitik gradyan). |
| `deney.py` | Bir senaryo ve başlangıç noktası için bütün modelleri çalıştırır. Senaryolar: `S_*` sansür şiddeti, `N_*` etiket gürültüsü, `D_CR*` doğal veri sansür tanımları, `LTR` ortam değişkeni eğitim penceresi uzunluğu. Tohum 20260427. |
| `deneyler.sh` | Bütün deney koşularını paralel çalıştırır. |
| `istatistik.py` | Ölçütler, iki aşamalı hiyerarşik önyükleme (B = 1000), Holm düzeltmesi, kıyas sapması ayrıştırması, heterojenlik regresyonu. |
| `ek_sinama.py` | Ek sağlamlık sınamaları: seçim kaynaklı ortalamaya dönüş, havuzsuz tam bilgili kıyas (TB0), sıfır hedef stok payı, etiket hatasının satış durumuna göre dağılımı, denetim paydası ve süre havuzu ayrıntıları. |
| `sekil_kavram.py`, `sekiller.py` | Şekil 1–5. |
| `sayilar.py` | Analiz çıktılarını (`CIKTI` ortam değişkeni, varsayılan `cikti/`) okur ve sayıları Türkçe yazım biçimine çevirir. |
| `icerik_*.py`, `tablolar*.py`, `olustur.py` | Makale metni, tablolar ve dergi şablonu üzerine Word çıktısı. Metindeki her sayı `sayilar.py` üzerinden analiz çıktılarından okunur. |
| `baslik_sayfasi.py` | Kör hakem sürecinden ayrı yüklenen başlık sayfası. |
| `ek_tablolar.py` | Ek tabloları Word dosyası ve her tablo için CSV olarak yazar. |
| `kanit.py` | Her atıflı cümlenin destekleyen pasajını kaynağın özet metninde birebir arar ve sonucu `cikti/kanit_raporu.csv` dosyasına yazar. Yeniden çalıştırmak için özet metinleri `ozet/*.kaynak` adreslerinden alınıp `literatur/ozet/<doi>.txt` adıyla kaydedilmelidir. |

## Çalıştırma

Python 3.13 ile sınanmıştır (sürüm ayrıntıları Ek Tablo 5 içindedir).

```
pip install -r gereksinimler.txt
unzip veri/Retail_Transactions_and_Stocks_Data.zip -d veri/ham
bash analiz/yeniden_uret.sh "veri/ham/Retail Transactions and Stocks Data" cikti_yeni teslim_yeni [dergi_sablonu.docx]
```

Şablon verilmezse analizler, şekiller ve ek tablolar üretilir, makale ve başlık sayfası adımları atlanır. Deney koşuları dört paralel süreçle birkaç saat sürer. Başarısız bir koşu olursa `deneyler.sh` koşunun adını yazar ve betik durur. Bütün koşuların durumu `cikti_yeni/log/deneyler_ozet.txt` dosyasında tutulur.

Ara deney dosyaları (`cikti/deney/*.npz`) boyutları nedeniyle depoya eklenmemiştir ve `deneyler.sh` tarafından yeniden üretilir. Bu dosyalara `istatistik.py` ve `ek_sinama.py` ihtiyaç duyar. Şekil, ek tablo ve metin adımları depodaki `cikti/` klasörüyle doğrudan çalışır:

```
cd analiz
python3 -I sekiller.py ../cikti ../sekil_yeni
CIKTI=../cikti python3 -I ek_tablolar.py ../ekler_yeni
```

Word çıktısındaki denklemler için sistemde pandoc kurulu olmalıdır.

## Lisans

Kod [MIT lisansı](LICENSE) ile, çıktılar ve ek tablolar CC BY 4.0 ile paylaşılmaktadır. Ham veri sağlayıcının CC BY 4.0 lisansına tabidir.

## Atıf

Makale yayımlandığında künye bu bölüme eklenecektir. Veri setini kullanırken lütfen veri sağlayıcısına da atıf yapınız.
