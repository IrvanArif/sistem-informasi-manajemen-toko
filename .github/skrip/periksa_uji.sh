#!/usr/bin/env bash
# Gerbang pengganti disiplin uji-dulu (bab 10 §10.2).
#
# Proyek ini menulis kode lebih dulu dan ujinya menyusul. Yang menjaga agar
# uji tidak pernah tertinggal bukan urutan penulisan, melainkan gerbang ini:
# cabang yang mengubah aturan bisnis tanpa membawa uji akan ditolak.
set -euo pipefail

dasar="${1:-origin/main}"
berubah=$(git diff --name-only "$dasar"...HEAD)

layanan=$(echo "$berubah" | grep '^backend/app/layanan/' || true)
uji=$(echo "$berubah" | grep '^backend/tests/' || true)

if [[ -n "$layanan" && -z "$uji" ]]; then
  echo "GAGAL: aturan bisnis berubah tanpa uji yang menyertainya."
  echo
  echo "Berkas layanan yang berubah:"
  echo "$layanan" | sed 's/^/  /'
  echo
  echo "Tambahkan atau perbarui uji di backend/tests/ sebelum menggabungkan."
  exit 1
fi

echo "OK: tidak ada perubahan aturan bisnis yang tanpa uji."
