# -*- coding: utf-8 -*-
"""Şekil 1: araştırma modeli. Gözlem mekanizması, bilgi işleme zinciri ve hipotez yönleri (siyah beyaz).
Kullanım: python3 -I sekil_kavram.py <cikti.png>"""
import sys, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 7, 'mathtext.fontset': 'dejavuserif'})
out = sys.argv[1]
fig, ax = plt.subplots(figsize=(6.9, 3.6), dpi=600)
ax.set_xlim(0, 22); ax.set_ylim(0, 10.6); ax.axis('off')

def kutu(x, y, w, h, metin, kalin=False, gri=False):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle='round,pad=0.06', fc='0.88' if gri else 'white',
                                ec='black', lw=1.1 if kalin else 0.6))
    ax.text(x, y, metin, ha='center', va='center', fontsize=6.0)

def ok(p1, p2, ls='-', cs='arc3', lw=0.7):
    ax.annotate('', xy=p2, xytext=p1, arrowprops=dict(arrowstyle='-|>', color='black', lw=lw, ls=ls, connectionstyle=cs, mutation_scale=7))

# üst sıra: gözlem mekanizması
ax.text(0.2, 10.05, 'Gözlem mekanizması', fontsize=6.8, fontweight='bold')
kutu(2.3, 8.6, 3.6, 1.4, 'Gizil talep\n$D_t$')
kutu(7.9, 8.6, 4.6, 1.4, 'Gözlenen satış\n$Y_t=\\min(D_t,A_t)$', gri=True)
kutu(13.6, 8.6, 4.0, 1.4, 'Satışa hazır stok\n$A_t$')
kutu(19.2, 8.6, 4.6, 1.4, 'Gün sonu stok kaydı\n$O_t=A_t-Y_t$')
ok((4.1, 8.6), (5.6, 8.6)); ok((11.6, 8.6), (10.2, 8.6)); ok((15.6, 8.6), (16.9, 8.6))
ok((10.2, 9.1), (16.9, 9.1), cs='arc3,rad=-0.16')

# orta sıra: bilgi işleme zinciri
ax.text(0.2, 6.95, 'Bilgi işleme zinciri', fontsize=6.8, fontweight='bold')
kutu(19.2, 5.4, 4.6, 1.7, 'Sansür bayrağı\n$C_t=1(O_t\\leq 0)$\nölçüm anı denetimi')
kutu(12.55, 5.4, 7.7, 1.9, 'Sansür bilgisinin kullanımı\nM0 yok, M1 silme, M2 atama, M3 seri içi,\nM5 Kaplan-Meier, M6 sansürlü düzeltme,\nM4 havuzlu sansürlü olabilirlik', kalin=True)
kutu(4.3, 5.4, 4.2, 1.9, 'Gizil talep tahmini\n$\\hat{D}_t$\n(GY, KS, SSOS)')
ok((19.2, 7.9), (19.2, 6.35)); ok((16.9, 5.4), (16.4, 5.4)); ok((8.7, 5.4), (6.4, 5.4))
ok((7.9, 7.9), (10.5, 6.35), ls='--')

# alt sıra: karar
kutu(4.3, 2.0, 4.2, 1.5, 'Yenileme kararı\nhaftalık hedef stok $S_w$', gri=True)
kutu(12.6, 2.0, 5.4, 1.5, 'Karar kalitesi\nTK modeline göre pişmanlık')
kutu(19.2, 2.0, 4.6, 1.5, 'Stok kaydı hatası\nyanlış negatif (YN)\nyanlış pozitif (YP)')
ok((4.3, 4.45), (4.3, 2.75)); ok((6.4, 2.0), (9.9, 2.0))
ok((19.2, 2.75), (19.2, 4.45), ls='--')
ax.plot([2.2, 0.9, 0.9], [1.25, 1.25, 7.9], color='black', lw=0.7, ls=':'); ax.annotate('', xy=(1.4, 7.9), xytext=(0.9, 7.9),
    arrowprops=dict(arrowstyle='-|>', color='black', lw=0.7, ls=':', mutation_scale=7))
ax.text(0.55, 4.6, 'sipariş ve yenileme', fontsize=5.6, rotation=90, va='center')

# hipotez etiketleri
def hip(x, y, m):
    ax.text(x, y, m, fontsize=6.2, ha='center', va='center', bbox=dict(boxstyle='round,pad=0.12', fc='white', ec='black', lw=0.4))
hip(12.3, 7.15, 'H1 (−): sansür şiddeti → M0 yanlılığı')
hip(7.55, 4.0, 'H2a, H2b (−): M4 → |GY|, KS')
hip(13.0, 3.45, 'H3 (+): sansür oranı → M4 kazancı\ndenetim değişkenleri: OTA, DK², hacim')
hip(19.2, 3.6, 'H4a: YN (−), YP (+)\nH4b (−): M4R → |GY|')
hip(8.4, 1.05, 'H5 (−): M4 → pişmanlık')
fig.savefig(out, bbox_inches='tight', pad_inches=0.03); print(out)
