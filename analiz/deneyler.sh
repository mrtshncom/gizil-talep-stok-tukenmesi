#!/bin/bash
# Bütün deney koşularını paralel çalıştırır. Kullanım: bash deneyler.sh <cikti_klasoru> [paralel_sayi]
# Başarısız koşu varsa adları yazılır ve betik 1 koduyla çıkar.
set -e
cd "$(dirname "$0")"
C=$1; P=${2:-4}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p "$C/deney" "$C/log"
kos() {  # $1: paralel süreç sayısı, standart girdi: L:senaryo:başlangıç satırları
  xargs -P "$1" -I{} bash -c 'IFS=: read L s k <<< "{}"; f="'"$C"'/deney/${s}_k${k}"; [ "$L" != 112 ] && f="${f}_L${L}"; if [ -f "$f.npz" ]; then echo "var $f"; else LTR=$L python3 -I deney.py "'"$C"'" $s $k > "'"$C"'/log/${s}_k${k}_L${L}.log" 2>&1 && echo "bitti $s $k $L" || echo "HATA $s $k $L"; fi'
}
jobs=""
for s in S_orta N_FP20 N_FN20 N_FP10 N_FN10 N_FP05 N_FN05 S_dusuk S_yuksek D_CR1 D_CR3 D_CR2 D_CR4 D_CR5; do
  for k in 0 1 2 3; do jobs="$jobs 112:$s:$k"; done
done
for L in 56 999; do for k in 0 1 2 3; do jobs="$jobs $L:S_orta:$k"; done; done
echo $jobs | tr ' ' '\n' | kos "$P" | tee "$C/log/deneyler_ozet.txt"

# sıfır şişkin sürüm bellek yükü nedeniyle iki paralel süreçle ayrı çalıştırılır
jobs=""
for k in 0 1 2 3; do jobs="$jobs 112:S_ortaZ:$k"; done
echo $jobs | tr ' ' '\n' | kos 2 | tee -a "$C/log/deneyler_ozet.txt"

if grep -q '^HATA' "$C/log/deneyler_ozet.txt"; then
  echo "Başarısız koşular:"; grep '^HATA' "$C/log/deneyler_ozet.txt"; exit 1
fi
