# -*- coding: utf-8 -*-
"""Bulgular şekilleri (siyah beyaz, 600 dpi). Kullanım: python3 -I sekiller.py <cikti_klasor> <sekil_klasor>"""
import sys, os, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

C, S = sys.argv[1], sys.argv[2]
os.makedirs(S, exist_ok=True)
R = json.load(open(os.path.join(C, 'sonuclar.json')))
plt.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 8, 'axes.linewidth': 0.6, 'mathtext.fontset': 'dejavuserif',
                     'xtick.major.width': 0.6, 'ytick.major.width': 0.6, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.unicode_minus': True, 'savefig.dpi': 600, 'axes.prop_cycle': matplotlib.cycler(color=['black'])})
# siyah beyaz: modeller çizgi türü, işaret ve gri tonuyla ayrılır
STIL = {'M0': dict(c='0.0', ls='--', m='s', mfc='white'), 'M1': dict(c='0.35', ls=':', m='^', mfc='0.35'),
        'M2': dict(c='0.55', ls='-.', m='D', mfc='white'), 'M3': dict(c='0.6', ls=':', m='x', mfc='0.6'),
        'M5': dict(c='0.45', ls=(0, (5, 1, 1, 1)), m='P', mfc='white'), 'M6': dict(c='0.25', ls=(0, (1, 1)), m='*', mfc='0.25'),
        'M4': dict(c='0.0', ls='-', m='o', mfc='0.0'), 'M4R': dict(c='0.3', ls='-', m='v', mfc='white'),
        'M4S': dict(c='0.5', ls='--', m='h', mfc='0.5'), 'TB': dict(c='0.7', ls='-', m='', mfc='0.7')}
TARAMA = {'M0': '////', 'M1': '....', 'M2': '\\\\\\\\', 'M4': '', 'M4S': 'xxx', 'M5': '---', 'M6': 'ooo', 'TB': '++'}
DOLGU = {'M0': 'white', 'M1': 'white', 'M2': 'white', 'M4': '0.15', 'M4S': 'white', 'M5': 'white', 'M6': 'white', 'TB': '0.75'}
GEN = 12.0 / 2.54
yuzde = FuncFormatter(lambda v, _: ('−' if v < -1e-12 else '') + '%' + f'{abs(v) * 100:.0f}')
def ondalik(d): return FuncFormatter(lambda v, _: (f'{v:.{d}f}').replace('-', '−').replace('.', ','))

def kaydet(fig, ad):
    fig.savefig(os.path.join(S, ad + '.png'), bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)

def cizgi(ax, x, y, m, lw=None):
    s = STIL[m]
    ax.plot(x, y, color=s['c'], ls=s['ls'], marker=s['m'] or None, ms=4, mfc=s['mfc'], mec=s['c'], lw=lw or (1.5 if m == 'M4' else 1.0), label=m)

# Şekil 2: sansür şiddetine göre geri kazanım yanlılığı
fig, ax = plt.subplots(figsize=(GEN, GEN * 0.55))
sen = ['S_dusuk', 'S_orta', 'S_yuksek']
x = [R[s]['sansur_orani'] for s in sen]
for m in ['M0', 'M1', 'M2', 'M4', 'M4S', 'TB']:
    if all(m in R[s]['olcut'] for s in sen):
        cizgi(ax, x, [R[s]['olcut'][m]['gk_yanlilik'] for s in sen], m)
ax.axhline(0, color='0.6', lw=0.5, zorder=1)
ax.yaxis.set_major_formatter(yuzde)
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: '%' + f'{v * 100:.0f}'))
ax.set_xlabel('Eğitim penceresinde sansürlü gün oranı')
ax.set_ylabel('Geri kazanım yanlılığı (GY)')
ax.legend(ncol=6, frameon=False, loc='upper center', bbox_to_anchor=(0.5, 1.14), fontsize=7, handlelength=2.4, columnspacing=0.8)
kaydet(fig, 'sekil2_siddet')

# Şekil 3: sansür oranı dilimlerine göre geri kazanım yanlılığı (orta şiddet, sıfır dilimi dahil)
dil = R['S_orta']['sansur_dilim']
def et(d):
    if d['ust'] == 0: return '%0'
    return f"%{d['alt'] * 100:.0f}–%{min(d['ust'], 1) * 100:.0f}".replace('%0–', '>%0–')
fig, ax = plt.subplots(figsize=(GEN, GEN * 0.55))
ms = ['M0', 'M1', 'M2', 'M4', 'TB']
gw = 0.8 / len(ms)
for j, m in enumerate(ms):
    y = [d[m]['gk_yanlilik'] for d in dil]
    ax.bar(np.arange(len(dil)) + (j - (len(ms) - 1) / 2) * gw, y, width=gw * 0.92, color=DOLGU[m], label=m,
           edgecolor='black', linewidth=0.5, hatch=TARAMA[m])
ax.axhline(0, color='black', lw=0.5)
ax.set_xticks(np.arange(len(dil)))
ax.set_xticklabels([f'{et(d)}\n(n = {d["n"]:,})'.replace(',', ' ') for d in dil])
ax.yaxis.set_major_formatter(yuzde)
ax.set_xlabel('Serinin eğitim penceresindeki sansürlü gün oranı')
ax.set_ylabel('Geri kazanım yanlılığı (GY)')
ax.legend(ncol=5, frameon=False, loc='upper center', bbox_to_anchor=(0.5, 1.13), fontsize=7, handlelength=1.6, columnspacing=0.8)
kaydet(fig, 'sekil3_dilim')

# Şekil 4: etiket gürültüsü
g = R.get('gurultu', {})
if all(f'{t}{e}' in g for t in ('FN', 'FP') for e in ('05', '10', '20')):
    fig, axs = plt.subplots(1, 2, figsize=(GEN, GEN * 0.5), sharey=True)
    eta = [0, 0.05, 0.10, 0.20]
    for ax, tur, bas in zip(axs, ['FN', 'FP'], ['Yanlış negatif', 'Yanlış pozitif']):
        for m in ['M1', 'M2', 'M4', 'M4R']:
            y = [R['S_orta']['olcut'][m]['gk_yanlilik']] + [g[f'{tur}{e}'][m]['gk_yanlilik'] for e in ['05', '10', '20']]
            cizgi(ax, eta, y, m)
        ax.axhline(0, color='0.6', lw=0.5)
        ax.set_title(bas, fontsize=8)
        ax.set_xticks(eta); ax.set_xticklabels(['0', '0,05', '0,10', '0,20'])
        ax.set_xlabel(r'Etiket hata oranı $\eta$')
    axs[0].yaxis.set_major_formatter(yuzde)
    axs[0].set_ylabel('Geri kazanım yanlılığı (GY)')
    axs[1].legend(frameon=False, fontsize=7, loc='upper left', handlelength=2.4)
    fig.tight_layout(w_pad=0.6)
    kaydet(fig, 'sekil4_gurultu')

# Şekil 5: hizmet düzeyine göre test kâhinine (TK) göre pişmanlık, ölçeksiz ve devirli
fig, axs = plt.subplots(1, 2, figsize=(GEN, GEN * 0.52), sharey=True)
crs = [50, 75, 90, 95]
for ax, anah, bas in zip(axs, ['pisman_TK', 'pismand_TK'], ['Haftalık yenile-tamamla', 'Devirli stok']):
    for m in ['M0', 'M1', 'M2', 'M6', 'M4', 'M4S', 'TB']:
        if m in R['S_orta']['olcut']:
            cizgi(ax, range(len(crs)), [R['S_orta']['olcut'][m][f'{anah}{c}'] for c in crs], m)
    ax.axhline(0, color='0.6', lw=0.5)
    ax.set_title(bas, fontsize=8)
    ax.set_xticks(range(len(crs))); ax.set_xticklabels(['0,50', '0,75', '0,90', '0,95'], fontsize=7)
    ax.set_xlabel('Hizmet düzeyi $k = p/(p+h)$')
axs[0].set_ylabel('TK modeline göre pişmanlık')
axs[0].yaxis.set_major_formatter(ondalik(1))
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, ncol=7, frameon=False, fontsize=7, loc='upper center', bbox_to_anchor=(0.5, 1.07), handlelength=2.2, columnspacing=0.7)
fig.tight_layout(w_pad=0.6)
kaydet(fig, 'sekil5_karar')
print('tamam')
