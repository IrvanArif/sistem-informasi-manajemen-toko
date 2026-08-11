# 07. Kontrak API

Daftar ini adalah rancangan, bukan dokumentasi. Dokumentasi yang sesungguhnya dibangkitkan FastAPI dari model Pydantic dan tersedia di `/docs` — kalau keduanya berbeda, **yang benar adalah yang dibangkitkan**, dan bab ini yang harus diperbarui.

## 7.1 Ketentuan umum

**Awalan:** `/api/v1`

**Otentikasi:** `Authorization: Bearer <token_akses>` pada semua endpoint kecuali `/auth/masuk` dan `/auth/segarkan`.

**Uang** dikirim sebagai bilangan bulat JSON: `39500` berarti Rp39.500.

**Jumlah berdesimal dikirim sebagai string**, bukan angka: `"1.500"`, bukan `1.5`. Angka dalam JSON adalah pecahan biner 64-bit, dan mengirim `NUMERIC(14,3)` lewat sana berarti menerima kembali nilai yang tidak persis sama. String tidak punya masalah itu, dan Pydantic mengubahnya menjadi `Decimal` tanpa kehilangan apa pun.

**Waktu** dalam ISO 8601 berzona UTC: `2026-08-07T05:12:33Z`.

**Halaman:** `?halaman=1&per_halaman=50`, jawaban dibungkus `{ "data": [...], "total": 0, "halaman": 1, "per_halaman": 50 }`.

**Bentuk kesalahan** selalu sama:

```json
{
  "kode": "SATUAN_FAKTOR_TIDAK_SAH",
  "pesan": "Faktor satuan harus lebih besar dari 0",
  "detail": { "satuan_id": 12, "faktor": "0.000" }
}
```

`kode` untuk program, `pesan` untuk manusia dan **sudah berbahasa Indonesia** — antarmuka menampilkannya apa adanya, tidak menerjemahkan ulang.

## 7.2 Otentikasi

| Metode | Jalur | Guna |
|---|---|---|
| POST | `/auth/masuk` | `{nama_pengguna, sandi}` → `{token_akses, token_segar, pengguna}` |
| POST | `/auth/segarkan` | `{token_segar}` → token akses baru |
| POST | `/auth/keluar` | Mencabut token segar |
| GET | `/auth/saya` | Data pengguna berjalan berikut perannya |
| POST | `/auth/ubah-sandi` | `{sandi_lama, sandi_baru}` — untuk diri sendiri (AKS-04) |

### Pengelolaan pengguna — hanya peran `pemilik`

| Metode | Jalur | Guna |
|---|---|---|
| GET | `/pengguna` | Daftar akun berikut peran & statusnya |
| POST | `/pengguna` | Buat akun baru `{nama_pengguna, nama_lengkap, sandi, peran}` (AKS-01) |
| PATCH | `/pengguna/{id}` | Ubah nama, peran, atau `{aktif: false}` untuk menonaktifkan (AKS-02) |
| POST | `/pengguna/{id}/atur-ulang-sandi` | Pemilik menetapkan sandi baru (AKS-03) |

Tiga penjagaan yang ditegakkan di server, bukan di tampilan:

- Menonaktifkan akun atau menurunkan perannya **ditolak** bila itu menyisakan nol akun `pemilik` aktif → `422 PEMILIK_TERAKHIR` (AKS-05).
- Pengguna tidak bisa mengubah perannya sendiri, meski ia pemilik. Menaikkan peran selalu tindakan orang lain.
- Akun dengan sesi kas yang masih terbuka tidak bisa dinonaktifkan → `422 SESI_KAS_MASIH_TERBUKA`. Kas yang belum dicocokkan tidak boleh kehilangan penanggung jawabnya.

## 7.3 Sinkronisasi

| Metode | Jalur | Guna |
|---|---|---|
| GET | `/sinkron/katalog?sejak=&kursor=` | Produk, satuan, kategori yang berubah sejak waktu tertentu |

Jawaban:

```json
{
  "produk": [ … ],
  "satuan": [ … ],
  "kategori": [ … ],
  "kursor_berikut": "eyJpZCI6MTIzfQ",
  "waktu_server": "2026-08-07T05:12:33Z"
}
```

`waktu_server` disimpan perangkat sebagai penanda `sejak` berikutnya. Perangkat tidak pernah memakai jamnya sendiri untuk ini ([bab 05](05-sinkronisasi-offline.md) §5.4).

> **Endpoint ini menyaring `hpp` berdasarkan peran, sama seperti `/produk`.** Untuk pengguna berperan `kasir`, kolom `hpp` **tidak pernah ikut terkirim** — bukan dikirim lalu disembunyikan. Ini endpoint yang paling sering dipanggil perangkat kasir, jadi kelalaian di sini membocorkan harga modal lewat pintu yang paling ramai. Diperiksa oleh uji integrasi di [bab 10 §10.3](10-strategi-pengujian.md#103-tiga-lapis).

## 7.4 Katalog

| Metode | Jalur | Guna |
|---|---|---|
| GET | `/produk?cari=&kategori_id=&aktif=&perlu_dilengkapi=` | Daftar produk; `perlu_dilengkapi=true` memberi daftar hasil "tambah cepat" yang belum dirapikan, seperti yang ditautkan dari dashboard ([bab 06 §6.4](06-antarmuka.md#64-dashboard-pemilik-hp)) |
| POST | `/produk` | Produk baru berikut satuan dasarnya |
| GET | `/produk/{id}` | Satu produk berikut seluruh satuannya |
| PATCH | `/produk/{id}` | Ubah produk |
| POST | `/produk/kilat` | Tambah cepat saat transaksi (STK-05) — `{nama, harga}` |
| POST | `/produk/{id}/satuan` | Tambah satuan |
| PATCH | `/satuan/{id}` | Ubah satuan; menonaktifkan lewat `{aktif: false}` |
| POST | `/produk/impor/pratinjau` | Unggah CSV → laporan baris sah & gagal, **tanpa menyimpan apa pun** |
| POST | `/produk/impor/jalankan` | Unggah **berkas yang sama sekali lagi** → baris sah disimpan |
| GET | `/produk/{id}/kartu-stok?dari=&sampai=` | Seluruh mutasi satu produk |
| GET POST PATCH | `/kategori` | Kategori |

Pratinjau impor mengembalikan kegagalan per baris dengan nomor barisnya:

```json
{
  "sah": 132,
  "gagal": [
    { "baris": 47, "alasan": "Kolom harga_jual kosong" },
    { "baris": 58, "alasan": "Barcode 8991002101234 sudah dipakai produk lain" }
  ]
}
```

**Impor tidak menyimpan keadaan sementara di server.** Pratinjau memeriksa lalu melupakan; saat pemilik menekan "Jalankan", perangkat mengirim berkas yang sama sekali lagi dan server memeriksanya ulang dari nol.

Ini memang berarti berkasnya terkirim dua kali — tidak berarti apa-apa untuk CSV beberapa ratus baris. Yang dibeli dengan itu sepadan: tidak ada token yang bisa kedaluwarsa di tengah pekerjaan, tidak ada berkas yatim yang menumpuk, dan tidak ada pembersih berkala yang harus ditulis dan dirawat. Pemeriksaan ulang juga menangkap perubahan yang terjadi di sela dua langkah — misalnya barcode yang keburu dipakai produk lain.

Bila berkasnya berubah di antara kedua langkah, hasil "Jalankan" mengikuti berkas yang terakhir dikirim — dan jawabannya selalu menyebutkan ulang berapa baris yang masuk dan berapa yang gagal, sehingga pemilik tidak pernah menebak apa yang sebenarnya terjadi.

## 7.5 Stok

| Metode | Jalur | Guna |
|---|---|---|
| POST | `/penyesuaian-stok` | `{produk_id, jumlah, alasan}` — **alasan wajib** |
| GET | `/stok/menipis` | Produk di bawah `stok_minimum` |
| GET | `/stok/minus` | Produk berstok negatif |
| POST | `/opname` | Buat sesi opname `{kategori_id?}` |
| GET | `/opname/{id}` | Sesi berikut barisnya |
| PATCH | `/opname/{id}/item` | Isi stok fisik satu atau beberapa baris |
| POST | `/opname/{id}/posting` | Ubah selisih menjadi mutasi — **tidak bisa dibatalkan** |

## 7.6 Penjualan

**`POST /penjualan`** — endpoint terpenting di seluruh sistem, karena ia yang menerima antrean offline.

```json
{
  "uuid_klien": "0f9a1c3e-5b7d-4a21-9e88-2c4f6a1b0d33",
  "nomor_nota": "20260807-K1-0007",
  "sesi_kas_id": 12,
  "waktu_transaksi": "2026-08-07T05:12:33Z",
  "metode_bayar": "tunai",
  "diskon_nota": 0,
  "pembulatan": 0,
  "total": 39500,
  "dibayar": 50000,
  "kembalian": 10500,
  "item": [
    {
      "produk_id": 88,
      "satuan_id": 141,
      "jumlah": "3.000",
      "harga_satuan": 3500,
      "diskon": 0,
      "subtotal": 10500
    },
    {
      "produk_id": 22,
      "satuan_id": 30,
      "jumlah": "1.500",
      "harga_satuan": 14000,
      "diskon": 0,
      "subtotal": 21000
    },
    {
      "produk_baru": {
        "uuid_klien": "7c2e5a90-1d44-4f0b-8a3c-6b9e2f5d8a11",
        "nama": "Sabun Cuci Piring 400ml",
        "harga": 12000
      },
      "jumlah": "1.000",
      "harga_satuan": 12000,
      "diskon": 0,
      "subtotal": 12000
    }
  ]
}
```

Setiap baris membawa **`produk_id` + `satuan_id`** (produk yang sudah dikenal) **atau `produk_baru`** (hasil "tambah cepat", termasuk yang dibuat saat offline) — tidak pernah keduanya, dan tidak pernah kosong keduanya.

Perilaku server:

| Keadaan | Jawaban |
|---|---|
| `uuid_klien` nota belum ada | `201` — disimpan, stok dipotong |
| `uuid_klien` nota sudah ada | `200` — data yang tersimpan sebelumnya, **tanpa memotong stok lagi** |
| Baris ber-`produk_baru`, UUID produk belum ada | Produk `perlu_dilengkapi` dibuat beserta satuan dasarnya, dalam transaksi yang sama |
| Baris ber-`produk_baru`, UUID produk sudah ada | Produk yang sudah ada dipakai — tidak pernah tercipta kembar |
| Baris memuat `produk_id` **dan** `produk_baru` | `422` `RUJUKAN_PRODUK_GANDA` |
| Data tidak sah | `422` berikut `kode` dan `pesan` |

Server **menghitung ulang** `subtotal` dan `total` dari `harga_satuan` dan `jumlah`, lalu menolak bila hasilnya berbeda dari yang dikirim. Yang diterima apa adanya hanyalah `harga_satuan` — karena angka itulah yang tercetak di struk dan disepakati pembeli ([bab 05](05-sinkronisasi-offline.md) §5.5) — sedangkan penjumlahannya tidak boleh dipercayakan ke perangkat.

Server juga mengisi sendiri `hpp_saat_itu` tiap baris; perangkat tidak pernah mengirimkannya dan memang tidak memilikinya.

| Metode | Jalur | Guna |
|---|---|---|
| GET | `/penjualan?dari=&sampai=&nomor=&kasir_id=` | Daftar nota |
| GET | `/penjualan/{id}` | Satu nota berikut barisnya |
| POST | `/penjualan/{id}/retur` | `{item: [{item_penjualan_id, jumlah}], alasan}` |

## 7.7 Sesi kas

| Metode | Jalur | Guna |
|---|---|---|
| POST | `/sesi-kas` | Buka `{modal_awal}` |
| GET | `/sesi-kas/aktif` | Sesi terbuka milik pengguna berjalan |
| POST | `/sesi-kas/{id}/tutup` | `{kas_fisik, catatan?}` — ditolak bila selisih ≠ 0 tanpa catatan |
| GET | `/sesi-kas?dari=&sampai=` | Riwayat sesi |

## 7.8 Pembelian

| Metode | Jalur | Guna |
|---|---|---|
| GET POST | `/pemasok` | Daftar & tambah |
| PATCH | `/pemasok/{id}` | Ubah; menonaktifkan lewat `{aktif: false}` |
| GET POST | `/pembelian` | Daftar & buat draft |
| PATCH | `/pembelian/{id}` | Ubah — **hanya selama berstatus draft** |
| POST | `/pembelian/{id}/terima` | Stok bertambah, HPP dihitung ulang, faktur terkunci |
| POST | `/pembelian/{id}/pembayaran` | `{jumlah, tanggal, metode, catatan?}` |
| GET | `/pembelian/hutang?jatuh_tempo_sebelum=` | Hutang yang belum lunas |

`POST /pembelian/{id}/terima` mengembalikan saran harga jual baru untuk tiap produk yang harga belinya naik (BEL-05). **Saran tidak pernah diterapkan sendiri** — pemilik yang memutuskan lewat `PATCH /satuan/{id}`.

## 7.9 Laporan

Semuanya menerima `?format=csv` untuk ekspor (LAP-07).

| Metode | Jalur | Guna |
|---|---|---|
| GET | `/laporan/ringkasan?tanggal=` | Isi dashboard |
| GET | `/laporan/penjualan?dari=&sampai=&kelompok=hari\|produk\|kategori\|kasir` | Penjualan |
| GET | `/laporan/laba?dari=&sampai=` | Laba kotor |
| GET | `/laporan/persediaan` | Nilai persediaan berjalan |
| GET | `/laporan/terlaris?dari=&sampai=&urut=jumlah\|nilai` | Produk terlaris |
| GET | `/laporan/sesi-kas?dari=&sampai=` | Rekap sesi kas |

## 7.10 Pengaturan

| Metode | Jalur | Guna |
|---|---|---|
| GET | `/pengaturan` | Seluruh pengaturan |
| PATCH | `/pengaturan` | Ubah sebagian |

## 7.11 Daftar kode kesalahan

| Kode | Arti |
|---|---|
| `KREDENSIAL_SALAH` | Nama pengguna atau sandi keliru |
| `TIDAK_BERHAK` | Peran tidak mengizinkan tindakan ini |
| `PEMILIK_TERAKHIR` | Tindakan itu menyisakan nol akun `pemilik` aktif |
| `SESI_KAS_MASIH_TERBUKA` | Akun tidak bisa dinonaktifkan selagi sesi kasnya belum ditutup |
| `PERAN_SENDIRI` | Pengguna mencoba mengubah perannya sendiri |
| `SESI_KAS_BELUM_DIBUKA` | Transaksi tanpa sesi kas terbuka |
| `SESI_KAS_MASIH_ADA_ANTREAN` | Penutupan ditolak, antrean belum bersih |
| `SELISIH_KAS_BUTUH_CATATAN` | Selisih ≠ 0 tanpa catatan |
| `NOTA_GANDA` | `nomor_nota` sudah dipakai `uuid_klien` lain |
| `TOTAL_TIDAK_COCOK` | Hitungan ulang server berbeda dari yang dikirim |
| `RUJUKAN_PRODUK_GANDA` | Satu baris nota memuat `produk_id` sekaligus `produk_baru` |
| `SATUAN_FAKTOR_TIDAK_SAH` | Faktor ≤ 0 |
| `SATUAN_DASAR_TUNGGAL` | Percobaan membuat lebih dari satu satuan dasar |
| `BARCODE_TERPAKAI` | Barcode sudah dipakai satuan lain |
| `ALASAN_WAJIB` | Penyesuaian stok tanpa alasan |
| `PEMBELIAN_SUDAH_DITERIMA` | Faktur terkunci, tidak bisa diubah |
| `RETUR_MELEBIHI_ASAL` | Jumlah retur melampaui sisa baris nota |
| `RETUR_KEDALUWARSA` | Nota lebih tua dari `batas_hari_retur` |
| `OPNAME_SUDAH_DIPOSTING` | Sesi opname terkunci |
