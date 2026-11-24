# -*- coding: utf-8 -*-
"""Öz ve Abstract. Sayılar analiz çıktılarından okunur."""
from sayilar import *
from icerik_oz_sabit import BASLIK_TR, BASLIK_EN, KISA_BASLIK, AK_TR, AK_EN, BEYAN, DEPO
import math

_S = R['S_orta']; _O = _S['olcut']; _KA = _S['ks_ayristirma']
_SEV = ['S_dusuk', 'S_orta', 'S_yuksek']
_m0 = [R[s]['olcut']['M0']['gk_yanlilik'] for s in _SEV]
_m4u = math.ceil(max(abs(R[s]['olcut']['M4']['gk_yanlilik']) for s in _SEV) * 200) / 200
_kap = 1 - _O['M4']['pisman_TB90'] / _O['M0']['pisman_TB90']
_kaps = 1 - _O['M4S']['pisman_TB90'] / _O['M0']['pisman_TB90']
_kaps_tr = 'tamamını' if _kaps >= 0.995 else yz(_kaps, 0) + ' kadarını'
_kaps_en = 'all of it' if _kaps >= 0.995 else _en(_kaps, 0) + ' of it'

def _en(x, d=1):
    v = x * 100
    return ('−' if v < 0 else '') + f'{abs(v):.{d}f}%'

OZ_TR = (
    'Stok tükendiğinde satış kaydı talebin alt sınırına dönüşmekte ve satışla eğitilen tahmin modeli talebi eksik öğrenmektedir. '
    f'Çalışma, {n(V["magaza"])} mağaza ve {n(V["sku"])} stok biriminden oluşan açık erişimli bir perakende veri setinde, '
    'gizil talebin günlük satış ve gün sonu stok kayıtlarından öğrenilip öğrenilemeyeceğini sınamaktadır. '
    f'Stok kaydının gün sonu ölçümü olduğu stok akışı özdeşliğiyle sınanmış (ardışık kayıtlı {n(DN["anlam_ayni_gun"]["satis_gunu_n"])} satış gününün {yz(DN["anlam_ayni_gun"]["tam_eslesme"])} kadarında eşleşme), '
    'veri altı sınamada gerçek işlem kaydıyla tutarlı bulunmuş ve bilinen talep verinin kendi stok kapasiteleri ve tükenme süreleriyle yeniden sansürlenmiştir. '
    f'Satışı talep sayan model sansür şiddetine göre talebin {yz(-_m0[0])} ile {yz(-_m0[2])} arasındaki bölümünü kaybetmiş, '
    f'havuzlu sansürlü ampirik Bayes modeli yanlılığı {yz(_m4u)} sınırının altına indirmiş ve aynı mimariyle tam bilgiyle kurulan modele en yakın tahmini üretmiştir. '
    f'Tam bilgili kıyasa uzaklıktaki kazancın {yz(_KA["mimari_pay"], 0)} kadarı havuzlamadan gelmekte, geri kazanımdaki kazanç sansürlü gün oranı yüksek serilerde büyümektedir. '
    'Etiket hatasının türü yanlılığın yönünü belirlemekte, hata payı ise bu olabilirlik yapısında satış ve bayrak verisinden tahmin edilememektedir. '
    f'Haftalık yenilemede havuzlu sansürlü model tam bilgiye göre oluşan maliyet kaybının {yz(_kap, 0)} kadarını kapatmış, '
    f'sansürü yok sayan havuzlu model bu kaybın {_kaps_tr} kapattığı için maliyet kazancı havuzlamaya bağlanmıştır.')

OZ_EN = (
    'When an item stocks out, recorded sales become a lower bound on demand and a model trained on sales underestimates demand. '
    f'Using an open retail dataset of {V["magaza"]} stores and {V["sku"]:,} stock keeping units, this study tests whether latent demand can be learned '
    'from daily sales and end-of-day stock records. '
    f'A stock-flow identity confirmed that stock records are end-of-day measurements ({_en(DN["anlam_ayni_gun"]["tam_eslesme"])} agreement on {DN["anlam_ayni_gun"]["satis_gunu_n"]:,} sales days with consecutive records), '
    'six tests were consistent with a real transaction record, and known demand was re-censored with the data’s own stock capacities and stockout durations. '
    f'The model that treats sales as demand lost {_en(-_m0[0])} to {_en(-_m0[2])} of demand depending on censoring severity, '
    f'while the pooled censored empirical Bayes model kept the bias below {_en(_m4u)} and produced the forecast closest to a full-information benchmark of the same architecture. '
    f'About {_en(_KA["mimari_pay"], 0)} of the gain in distance to that benchmark came from pooling, and the recovery gain increased with the share of censored days. '
    'The type of label error determined the direction of bias, whereas under this likelihood the error share could not be estimated from sales and flags alone. '
    f'In weekly replenishment, the pooled censored model closed {_en(_kap, 0)} of the cost loss relative to full information, '
    f'but the pooled model ignoring censoring closed {_kaps_en}, so the cost gain stems from pooling.')
