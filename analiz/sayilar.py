# -*- coding: utf-8 -*-
"""Metinde geçen bütün sayılar bu modül üzerinden analiz çıktılarından okunur. Ondalık ayıracı virgüldür."""
import json, os
CIKTI = os.environ.get('CIKTI', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cikti'))
V = json.load(open(os.path.join(CIKTI, 'veri_bilgi.json')))
DN = json.load(open(os.path.join(CIKTI, 'denetim.json')))
EK = json.load(open(os.path.join(CIKTI, 'ek_denetim.json')))
ST = json.load(open(os.path.join(CIKTI, 'sentetik_test.json')))
_e = os.path.join(CIKTI, 'ek_sinama.json')
ES = json.load(open(_e)) if os.path.exists(_e) else {}
_r = os.path.join(CIKTI, 'sonuclar.json')
R = json.load(open(_r)) if os.path.exists(_r) else {}

def n(x):
    """Tam sayı, binler basamağı boşlukla."""
    x = int(round(x))
    s = f'{abs(x):,}'.replace(',', '\u00a0')
    return ('−' if x < 0 else '') + s
def f(x, d=2):
    s = f'{x:.{d}f}'
    return s.replace('-', '−').replace('.', ',')
def yz(x, d=1, isaret=False):
    """Oranı yüzdeye çevirir: %12,3 biçiminde."""
    v = x * 100
    s = f'{abs(v):.{d}f}'
    tam, _, kes = s.partition('.')
    if len(tam) > 3: tam = f'{int(tam):,}'.replace(',', '\u00a0')       # binler basamağı bölünmez boşlukla
    sv = tam + (',' + kes if kes else '')
    if v < 0 and float(s) != 0: return '−\u2060%' + sv                 # işaret ile yüzde arasında satır kırılmaz
    if isaret and v > 0 and float(s) != 0: return '+\u2060%' + sv
    return '%' + sv
def p(x):
    return 'p < 0,001' if x < 0.001 else 'p = ' + f'{x:.3f}'.replace('.', ',')
import numpy as _np
def len_bosluk():
    return len(_np.load(os.path.join(CIKTI, 'bosluk_sureleri.npy')))
