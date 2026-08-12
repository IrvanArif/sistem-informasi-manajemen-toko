# Kebijakan Repositori: Apa yang Boleh dan Tidak Boleh Diunggah

Repositori ini **publik**. Siapa pun bisa membacanya, dan mesin pencari
mengindeksnya. Setiap berkas yang masuk harus lolos satu pertanyaan:

> Kalau berkas ini dibaca orang yang tidak dikenal, apakah ada yang rusak?

## 1. Boleh diunggah

| Apa | Kenapa aman |
|---|---|
| Kode sumber `backend/` dan `frontend/` | Tidak memuat rahasia. Seluruh rahasia dibaca dari variabel lingkungan. |
| Dokumen perancangan `docs/` | Rancangan bukan rahasia. Keamanan sistem ini tidak bergantung pada kerahasiaan rancangannya. |
| Migrasi `backend/migrasi/` | Bentuk tabel, bukan isinya. |
| Uji `backend/tests/`, `frontend/tests/` | Memakai nilai khusus uji yang tidak berlaku di mana pun. |
| `backend/.env.contoh` | Hanya nama variabel dan nilai penanda, tanpa nilai sungguhan. |
| `backend/uv.lock`, `frontend/package-lock.json` | Daftar versi dan sidik jari paket. Justru berguna diunggah agar pemasangan bisa diulang persis. |
| Alur CI `.github/` | Tidak memuat nilai rahasia. Rahasia CI, bila kelak ada, disimpan di pengaturan repositori. |

## 2. Tidak boleh diunggah

| Apa | Pola di `.gitignore` | Kalau bocor |
|---|---|---|
| `backend/.env` | `.env`, `.env.*` | `RAHASIA_JWT` bocor. Siapa pun bisa menerbitkan token yang diterima sistem, lalu masuk sebagai pemilik tanpa sandi. |
| `kredensial-lokal.md` | `kredensial*` | Seluruh sandi tercatat di sana. |
| `backend/data_pg/` | `backend/data_pg/` | Isi basis data: akun, dan kelak seluruh transaksi toko. |
| Cadangan basis data | `*.sql`, `*.dump`, `cadangan/` | Sama seperti di atas, lengkap. |
| Kunci apa pun | `*.pem`, `*.key`, `*.p12`, `*.age`, `*.gpg` | Bergantung kuncinya, dan tidak ada yang ringan. |
| `frontend/node_modules/`, `frontend/dist/` | sudah diabaikan | Bukan rahasia, tetapi hasil bangkitan dan membengkakkan repositori. |
| `backend/openapi.json` | `backend/openapi.json` | Bukan rahasia, tetapi hasil bangkitan. Dibuat ulang dengan `npm run tipe`. |

## 3. Cara memeriksa sebelum mengunggah

Jalankan ini sebelum `git push`, terutama setelah menambah berkas baru:

```bash
cd ~/Documents/Toko

# 1. Apa yang akan masuk?
git status --porcelain --untracked-files=all

# 2. Pastikan berkas rahasia benar-benar diabaikan
for f in backend/.env kredensial-lokal.md backend/data_pg; do
  printf "%-26s %s\n" "$f" \
    "$(git check-ignore -q "$f" && echo diabaikan || echo 'BAHAYA: akan masuk')"
done

# 3. Cari nilai yang menyerupai rahasia di berkas yang dilacak git
git ls-files -z | xargs -0 grep -lE \
  '(-----BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|://[^/[:space:]:]+:[^/[:space:]@]+@)' \
  2>/dev/null || echo "tidak ada yang menyerupai rahasia"
```

## 4. Kalau rahasia telanjur terunggah

Menghapusnya di commit berikutnya **tidak cukup**. Riwayat git menyimpan
seluruh versi lama, dan repositori publik kemungkinan sudah disalin serta
diindeks dalam hitungan menit.

Urutan yang benar:

1. **Anggap rahasianya sudah bocor.** Ganti nilainya sekarang juga:
   terbitkan `RAHASIA_JWT` baru, ganti sandi, cabut token.
2. Baru bersihkan riwayatnya (`git filter-repo` atau hapus lalu buat ulang
   repositorinya).
3. Catat kejadiannya di berkas ini agar tidak terulang.

Urutannya tidak boleh dibalik. Membersihkan riwayat lebih dulu memberi
rasa aman yang keliru, sementara nilai yang bocor masih berlaku.

## 5. Yang sengaja dibiarkan terbuka

Bab keamanan, kontrak API, ambang pembatasan percobaan masuk, dan titik
lemah yang diakui sendiri semuanya terbaca umum. Itu keputusan sadar,
bukan kelalaian.

Keamanan sistem ini bertumpu pada otentikasi, hak akses per rute, hash
sandi, dan pembatasan percobaan masuk. Tidak satu pun bergantung pada
kerahasiaan rancangannya. Rancangan yang hanya aman selama tidak dibaca
orang bukanlah rancangan yang aman.

Yang tetap ditutup di lingkungan sungguhan hanyalah `/docs` dan
`/openapi.json`, karena keduanya memberi daftar siap pakai yang membuat
penjelajahan otomatis menjadi murah. Itu mengurangi kemudahan, bukan
menggantikan penjagaan.
