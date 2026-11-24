# -*- coding: utf-8 -*-
"""Kaynak anahtarı ile DOI eşlemesi ve IEEE biçiminde kaynakça satırı üretimi.
Bütün alanlar Crossref veya DataCite kayıtlarından okunur. Crossref kaydında eksik kalan alanlar (yazar adı,
sayfa aralığı) EKSIK sözlüğünde kaynağın kendi yayımlanmış künyesinden tamamlanır.
Veri seti kaynağı yazarların verdiği biçimde kullanılır."""
import json, os, re, html

LIT = os.environ.get('LIT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'literatur'))

DOI = {
 'fildes22': '10.1016/j.ijforecast.2019.06.004', 'corsten03': '10.1108/09590550310507731', 'conrad76': '10.1057/jors.1976.13',
 'anupindi98': '10.1287/mksc.17.4.406', 'wecker78': '10.1287/mnsc.24.10.1043',
 'agrawal96': '10.1002/(SICI)1520-6750(199609)43:6<839::AID-NAV4>3.0.CO;2-5',
 'nahmias94': '10.1002/1520-6750(199410)41:6<739::aid-nav3220410605>3.0.co;2-a',
 'besbes13': '10.1287/mnsc.1120.1654', 'jain15': '10.1287/opre.2014.1326', 'huh11': '10.1287/opre.1100.0906',
 'sachs14': '10.1016/j.ijpe.2013.04.039', 'trapero24': '10.1016/j.ijforecast.2023.09.004', 'wang25': '10.48550/arXiv.2505.16319',
 'yin26': '10.3390/su18157642', 'dehoratius08': '10.1287/mnsc.1070.0789', 'shabani21': '10.1016/j.ijpe.2021.108111',
 'kang05': '10.1080/07408170590969861', 'mersereau15': '10.1287/msom.2015.0520', 'chehrazi25': '10.1287/msom.2023.0274',
 'theodorou25': '10.1016/j.ejor.2024.12.033', 'vanderhaar24': '10.1016/j.ejor.2024.07.004', 'lawless87': '10.2307/3314912',
 'morris83': '10.1080/01621459.1983.10477920', 'dempster77': '10.1111/j.2517-6161.1977.tb01600.x', 'bergmeir18': '10.1016/j.csda.2017.11.003',
 'hyndman06': '10.1016/j.ijforecast.2006.03.001', 'kolassa16': '10.1016/j.ijforecast.2015.12.004', 'gneiting07a': '10.1198/016214506000001437',
 'gneiting07b': '10.1111/j.1467-9868.2007.00587.x', 'khouja99': '10.1016/S0305-0483(99)00017-1', 'efron79': '10.1214/aos/1176344552',
 'field07': '10.1111/j.1467-9868.2007.00593.x', 'aickin96': '10.2105/AJPH.86.5.726', 'syntetos05': '10.1057/palgrave.jors.2601841',
 'pandas': '10.25080/Majora-92bf1922-00a', 'numpy': '10.1038/s41586-020-2649-2', 'scipy': '10.1038/s41592-019-0686-2',
 'statsmodels': '10.25080/Majora-92bf1922-011', 'matplotlib': '10.1109/MCSE.2007.55', 'veri': '10.17632/27x8mjm8k4.1',
 'snyder12': '10.1016/j.ijforecast.2011.03.009',
 'galbraith74': '10.1287/inte.4.3.28', 'wang96': '10.1080/07421222.1996.11518099', 'delone03': '10.1080/07421222.2003.11045748',
 'syntetos05b': '10.1016/j.ijforecast.2004.10.001', 'lambert92': '10.2307/1269547', 'mullahy86': '10.1016/0304-4076(86)90002-3',
 'conlon13': '10.1257/mic.5.4.1', 'musalem10': '10.1287/mnsc.1100.1170', 'kaplan58': '10.1080/01621459.1958.10501452',
 'croston72': '10.1057/jors.1972.50', 'tobin58': '10.2307/1907382',
}

EKSIK = {
 '10.1080/07421222.2003.11045748': dict(author=[{'family': 'DeLone', 'given': 'William H.'}, {'family': 'McLean', 'given': 'Ephraim R.'}]),
 '10.2307/1269547': dict(page='1-14'),
 '10.2307/1907382': dict(page='24-36'),
}

VERI_METNI = 'Smith, Jimmy (2026), “Retail Transactions and Stocks Data”, Mendeley Data, V1, doi: 10.17632/27x8mjm8k4.1'

def dosya(doi):
    return os.path.join(LIT, 'cr', doi.replace('/', '_') + '.json')

def kayit(anahtar):
    doi = DOI[anahtar]
    yol = dosya(doi)
    if not os.path.exists(yol):
        yol = dosya(doi.lower())
    return json.load(open(yol))

def _temiz(s):
    s = html.unescape(re.sub(r'<[^>]+>', '', s or ''))
    return re.sub(r'\s+', ' ', s).strip()

def _bas_harf(ad):
    parcalar = re.split(r'[\s]+', ad.strip())
    out = []
    for p in parcalar:
        if not p: continue
        if '-' in p:
            out.append('-'.join(q[0] + '.' for q in p.split('-') if q))
        else:
            out.append(p[0] + '.')
    return ' '.join(out)

def _yazarlar(liste):
    adlar = []
    for a in liste:
        if 'family' in a or 'familyName' in a:
            soy = a.get('family') or a.get('familyName'); ad = a.get('given') or a.get('givenName') or ''
            adlar.append((_bas_harf(ad) + ' ' + soy).strip())
        else:
            adlar.append(a.get('name'))
    if len(adlar) > 6:
        return adlar[0] + ' et al.'
    if len(adlar) == 1: return adlar[0]
    if len(adlar) == 2: return adlar[0] + ' and ' + adlar[1]
    return ', '.join(adlar[:-1]) + ', and ' + adlar[-1]

def alanlar(anahtar):
    """IEEE satırının parçalarını döndürür: (yazarlar, başlık, kaynak, ayrıntı, yıl, doi)."""
    x = kayit(anahtar); doi = DOI[anahtar]
    if 'datacite' in x:
        a = x['datacite']['data']['attributes']
        yazar = _yazarlar(a['creators']); baslik = _temiz(a['titles'][0]['title'])
        yil = str(a['publicationYear'])
        kaynak = a.get('publisher')
        if isinstance(kaynak, dict): kaynak = kaynak.get('name')
        ayr = ''
        if doi.startswith('10.48550'):
            kaynak = 'arXiv preprint'; ayr = 'arXiv:' + doi.split('arXiv.')[-1]
        return yazar, baslik, kaynak, ayr, yil, doi
    m = dict(x['message']); m.update(EKSIK.get(doi, {}))
    yazar = _yazarlar(m.get('author', []))
    baslik = _temiz(m['title'][0]).rstrip('.')
    kaynak = _temiz((m.get('container-title') or [''])[0])
    if not kaynak and m.get('type') == 'proceedings-article':
        kaynak = _temiz((m.get('event') or {}).get('name', ''))
    tarih = (m.get('published-print') or m.get('published') or m.get('issued'))['date-parts'][0]
    yil = str(tarih[0])
    cilt = m.get('volume'); sayi = m.get('issue'); sayfa = m.get('page') or m.get('article-number')
    ayr = []
    if cilt: ayr.append(cilt + (f'({sayi})' if sayi else ''))
    if sayfa: ayr.append(sayfa.replace('-', '–'))
    return yazar, baslik, kaynak, ', '.join(ayr), yil, doi

def ieee(anahtar):
    """Kaynakça satırını (parça, italik mi) listesi ve DOI bağlantısı olarak döndürür."""
    if anahtar == 'veri':
        return [('J. Smith, “Retail Transactions and Stocks Data,” ', False), ('Mendeley Data', True), (', V1, 2026.', False)], 'https://doi.org/' + DOI['veri']
    yazar, baslik, kaynak, ayr, yil, doi = alanlar(anahtar)
    parca = [(f'{yazar}, “{baslik},” ', False), (kaynak, True), ((', ' + ayr if ayr else '') + f', {yil}.', False)]
    return parca, 'https://doi.org/' + doi

if __name__ == '__main__':
    for k in DOI:
        p, u = ieee(k)
        print(k, ''.join(t for t, _ in p), u)


def _apa_yazarlar(liste):
    adlar = []
    for a in liste:
        if 'family' in a or 'familyName' in a:
            soy = a.get('family') or a.get('familyName'); ad = a.get('given') or a.get('givenName') or ''
            adlar.append((soy + ', ' + _bas_harf(ad)).strip(', '))
        else:
            adlar.append(a.get('name'))
    if len(adlar) == 1: return adlar[0]
    if len(adlar) <= 20: return ', '.join(adlar[:-1]) + ', & ' + adlar[-1]
    return ', '.join(adlar[:19]) + ', ... ' + adlar[-1]


def apa(anahtar):
    """APA 7 biçiminde kaynakça satırı: (parça, italik mi) listesi ve DOI bağlantısı."""
    doi = DOI[anahtar]
    if anahtar == 'veri':
        return [('Smith, J. (2026). ', False), ('Retail transactions and stocks data', True), (' (V1) [Veri seti]. Mendeley Data. ', False)], 'https://doi.org/' + doi
    x = kayit(anahtar)
    if 'datacite' in x:
        a = x['datacite']['data']['attributes']
        yazar = _apa_yazarlar(a['creators']); baslik = _temiz(a['titles'][0]['title']).rstrip('.')
        yil = str(a['publicationYear'])
        if doi.startswith('10.48550'):
            return [(f'{yazar} ({yil}). ', False), (baslik, True), (f'. arXiv. ', False)], 'https://doi.org/' + doi
        kaynak = a.get('publisher'); kaynak = kaynak.get('name') if isinstance(kaynak, dict) else kaynak
        return [(f'{yazar} ({yil}). ', False), (baslik, True), (f'. {kaynak}. ', False)], 'https://doi.org/' + doi
    m = dict(x['message']); m.update(EKSIK.get(doi, {}))
    yazar = _apa_yazarlar(m.get('author', []))
    baslik = _temiz(m['title'][0]).rstrip('.')
    kaynak = _temiz((m.get('container-title') or [''])[0])
    tarih = (m.get('published-print') or m.get('published') or m.get('issued'))['date-parts'][0]
    yil = str(tarih[0])
    cilt = m.get('volume'); sayi = m.get('issue'); sayfa = m.get('page') or m.get('article-number')
    if m.get('type') in ('book-chapter',):
        ed = _temiz((m.get('container-title') or [''])[0])
        return [(f'{yazar} ({yil}). {baslik}. In ', False), (ed, True), (f' (pp. {sayfa.replace("-", "–")}). {m.get("publisher", "")}. ' if sayfa else f'. {m.get("publisher", "")}. ', False)], 'https://doi.org/' + doi
    parca = [(f'{yazar} ({yil}). {baslik}. ', False), (kaynak, True)]
    if cilt:
        parca.append((', ', False)); parca.append((cilt, True))
        if sayi: parca.append((f'({sayi})', False))
    if sayfa: parca.append((', ' + sayfa.replace('-', '–'), False))
    parca.append(('. ', False))
    return parca, 'https://doi.org/' + doi
