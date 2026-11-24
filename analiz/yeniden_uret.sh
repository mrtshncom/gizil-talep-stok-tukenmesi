#!/bin/bash
# Bütün analizi ham veriden yeniden üretir.
# Kullanım: bash yeniden_uret.sh <ham_veri_klasoru> <cikti_klasoru> <teslim_klasoru> [sablon.docx]
# Şablon verilmezse makale ve başlık sayfası dışındaki bütün çıktılar (analizler, şekiller, ek tablolar) üretilir.
set -e
HAM=$(realpath "$1"); C=$(realpath -m "$2"); T=$(realpath -m "$3"); SAB=${4:+$(realpath "$4")}
cd "$(dirname "$0")"
mkdir -p "$C/sekil" "$T"
python3 -I veri_hazirla.py "$HAM" "$C"
python3 -I denetim.py "$C"
python3 -I ek_denetim.py "$C" "$C/ek_denetim.json"
python3 -I sentetik_test.py "$HAM" "$C/sentetik_test.json"
bash deneyler.sh "$C" 4
python3 -I istatistik.py "$C"
python3 -I ek_sinama.py "$C"
python3 -I sekil_kavram.py "$C/sekil/sekil1_model.png"
python3 -I sekiller.py "$C" "$C/sekil"
export CIKTI="$C"
python3 -I kanit.py
python3 -I ek_tablolar.py "$T/ekler"
if [ -n "$SAB" ]; then
  python3 -I olustur.py "$SAB" "$T/Makale.docx" "$C/sekil"
  python3 -I baslik_sayfasi.py "$SAB" "$T/Baslik_Sayfasi.docx"
fi
