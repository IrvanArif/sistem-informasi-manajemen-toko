# 02. Arsitektur

## 2.1 Tiga bagian, batas yang tegas

| Bagian | Isi | Tanggung jawab | Yang **bukan** tanggung jawabnya |
|---|---|---|---|
| `backend/` | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL | Seluruh aturan bisnis: stok, HPP, laba, laporan, otentikasi | Tampilan, tata letak, keadaan layar |
| `frontend/` | React 19, TypeScript, Vite, PWA | Seluruh antarmuka; menyimpan salinan katalog dan antrean penjualan | Menghitung apa pun yang bersifat uang atau stok akhir |
| kontrak | OpenAPI dari FastAPI → tipe TypeScript | Menjaga kedua sisi tetap sepakat | — |

Aturan yang memisahkan keduanya: **browser boleh menghitung untuk ditampilkan, server yang menghitung untuk disimpan.** Keranjang belanja boleh menjumlahkan total agar kasir melihat angkanya seketika, tapi angka yang tersimpan adalah hasil hitungan ulang di server. Kalau keduanya berbeda, itu bug — dan uji akan menangkapnya.

## 2.2 Kenapa SPA, bukan render di server

Halaman yang dirender di server membutuhkan server saat dibuka. Itu persis sumber daya yang hilang ketika internet mati — sementara justru saat itulah kasir paling butuh aplikasinya terbuka.

Tidak ada satu pun kebutuhan di [bab 01](01-kebutuhan.md) yang memerlukan render server: tidak ada halaman publik, tidak ada kebutuhan SEO, tidak ada berbagi tautan ke luar. → [ADR-0001](../adr/0001-spa-bukan-render-server.md)

## 2.3 Struktur repositori

```
toko/
├── backend/
│   ├── app/
│   │   ├── main.py                 titik masuk FastAPI
│   │   ├── konfigurasi.py          pengaturan dari environment
│   │   ├── basisdata.py            sesi & mesin SQLAlchemy
│   │   ├── model/                  tabel SQLAlchemy
│   │   ├── skema/                  model Pydantic (bentuk data masuk & keluar)
│   │   ├── layanan/                ← ATURAN BISNIS ADA DI SINI
│   │   │   ├── stok.py             mutasi, saldo, konversi satuan
│   │   │   ├── hpp.py              rata-rata bergerak
│   │   │   ├── penjualan.py        transaksi, idempotensi, retur
│   │   │   ├── pembelian.py        penerimaan barang
│   │   │   ├── opname.py
│   │   │   └── laporan.py
│   │   ├── rute/                   endpoint HTTP — tipis, tanpa logika
│   │   └── keamanan/               hash sandi, token, hak akses
│   ├── migrasi/                    Alembic
│   ├── skrip/                      perintah sekali jalan
│   ├── tests/
│   ├── data_pg/                    data PostgreSQL lokal (diabaikan git)
│   └── pyproject.toml              dikelola uv
│
├── frontend/
│   ├── src/
│   │   ├── fitur/
│   │   │   ├── kasir/              layar POS, keranjang, pembayaran
│   │   │   ├── produk/
│   │   │   ├── pembelian/
│   │   │   ├── opname/
│   │   │   └── laporan/
│   │   ├── lokal/                  ← LAPISAN OFFLINE ADA DI SINI
│   │   │   ├── basisdata.ts        skema Dexie / IndexedDB
│   │   │   ├── replika.ts          sinkron katalog turun
│   │   │   └── antrean.ts          outbox penjualan naik
│   │   ├── api/                    klien HTTP + tipe hasil bangkitan
│   │   ├── komponen/               komponen bersama
│   │   └── main.tsx
│   └── package.json
│
├── docs/
│   ├── spesifikasi.md              spesifikasi induk
│   ├── perancangan/                bab-bab ini
│   ├── rencana/                    rencana implementasi per tahap
│   └── adr/                        catatan keputusan arsitektur
│
└── .github/workflows/              uji, bangun, cadangan harian
```

**Aturan struktur yang dijaga:**

- `rute/` tidak boleh mengandung aturan bisnis. Tugasnya menerima permintaan, memanggil `layanan/`, mengembalikan jawaban. Kalau ada `if` yang berhubungan dengan stok atau uang di dalam `rute/`, itu salah tempat.
- `layanan/` tidak boleh tahu soal HTTP. Fungsi di sana menerima objek biasa dan sesi basis data, sehingga bisa diuji tanpa menyalakan server.
- `frontend/lokal/` adalah satu-satunya tempat yang menyentuh IndexedDB. Komponen tampilan tidak pernah memanggilnya langsung.

Pemisahan ini bukan formalitas: ia yang membuat aturan bisnis bisa diuji dengan cepat, dan membuat berkas tetap cukup kecil untuk dipahami sekali baca.

## 2.4 Pilihan teknis dan alasannya

| Pilihan | Alasan | Alternatif yang ditolak |
|---|---|---|
| PostgreSQL | `NUMERIC` sejati untuk jumlah pecahan, transaksi kuat, penguncian baris | SQLite, yang tidak punya keduanya |
| `pgserver` | Menjalankan PostgreSQL 16 dari dalam lingkungan Python, tanpa memasang apa pun ke sistem ([ADR-0009](../adr/0009-postgresql-tersemat-tanpa-docker.md)) | Docker Compose, PostgreSQL lewat `apt` |
| SQLAlchemy 2.0 | Kendali penuh atas kueri laporan yang agak rumit | ORM yang menyembunyikan SQL |
| Alembic | Perubahan skema tercatat dan bisa dibalik | Ubah tabel secara manual |
| Pydantic v2 | Validasi masuk-keluar + sumber OpenAPI | Validasi manual |
| `uv` | Pemasangan cepat, kunci versi tegas | pip + requirements.txt |
| Dexie | Pembungkus IndexedDB yang manusiawi | IndexedDB mentah |
| `vite-plugin-pwa` | Service worker tanpa menulis sendiri | Workbox manual |
| Tailwind + shadcn/ui | Komponen bisa disalin dan diubah, bukan paket kaku | Kerangka komponen yang sulit dikustom |
| Argon2 | Standar hash sandi saat ini | bcrypt, MD5 |

Semuanya berlisensi MIT, Apache, ISC, PSF, atau PostgreSQL License. Tidak ada yang berbayar.

## 2.5 Uang dan angka

Dua aturan yang berlaku di seluruh sistem, tanpa pengecualian:

**Uang selalu bilangan bulat rupiah.** Kolom `BIGINT` di basis data, `int` di Python, `number` bulat di TypeScript. Rupiah tidak punya satuan di bawah rupiah, jadi tidak ada yang perlu disimpan sebagai pecahan.

Ada **satu pengecualian**: HPP disimpan `NUMERIC(14,4)`, karena ia tarif turunan yang dikalikan faktor satuan — bukan jumlah yang dibayarkan. Alasan lengkapnya di [bab 03 §3.4](03-model-data.md#34-kenapa-hpp-boleh-berdesimal-padahal-uang-tidak).

**Jumlah barang selalu `NUMERIC(14,3)`**, dipetakan ke `decimal.Decimal` di Python. **Tidak pernah `float`.** Alasannya bukan teori: dalam `float`, `0.1 + 0.2` menghasilkan `0.30000000000000004`. Selisih sekecil itu menumpuk lintas ribuan transaksi dan akhirnya muncul sebagai selisih stok yang tidak bisa dijelaskan siapa pun.

Pembulatan hasil `harga × jumlah` memakai pembulatan ke atas untuk setengah (`ROUND_HALF_UP`) ke rupiah terdekat, dilakukan **satu kali** di tingkat baris nota — bukan berulang di tiap langkah, karena pembulatan berulang menggeser hasil.

## 2.6 Penempatan

| Lapisan | Layanan | Sifat |
|---|---|---|
| Tampilan statis | Cloudflare Pages | Gratis permanen, tanpa syarat khusus |
| API Python | Render (lapisan gratis) | Tidur setelah 15 menit menganggur, bangun ~50 detik |
| PostgreSQL | Neon (lapisan gratis) | 0,5 GB — cukup untuk beberapa tahun transaksi toko ini |
| Cadangan | GitHub Actions terjadwal | `pg_dump` harian, disimpan terenkripsi |

Soal tidur-bangun Render: **antrean offline kebetulan menutupi persis masalah itu.** Transaksi pertama di pagi hari tidak menunggu server bangun — ia masuk antrean lokal dan terkirim sendiri beberapa puluh detik kemudian. Kasir tidak pernah melihat penantian itu.

Perkiraan ukuran data: satu nota ± 200 byte, satu baris nota ± 150 byte. Pada 100 transaksi/hari dengan rata-rata 5 barang, setahun menghasilkan sekitar 40 MB sebelum indeks. Batas 0,5 GB memberi ruang bertahun-tahun.

Penempatan memakai `Dockerfile` yang **dibangun di sisi penyedia**, sehingga pindah ke penyedia lain, atau ke komputer toko sendiri, tidak menuntut penulisan ulang. Docker tidak perlu terpasang di komputer pengembangan mana pun. → [ADR-0007](../adr/0007-lapisan-gratis-dan-portabilitas.md), [ADR-0009](../adr/0009-postgresql-tersemat-tanpa-docker.md)

Untuk pengembangan dan pengujian, PostgreSQL dijalankan oleh `pgserver` dari dalam lingkungan Python proyek. Mesin basis datanya tetap PostgreSQL 16 yang sama seperti di penempatan; yang berbeda hanya cara menyalakannya.

## 2.7 Yang sengaja tidak dipakai

Microservices, Redis, antrean pesan, Kubernetes, GraphQL, dan basis data terpisah untuk laporan.

Satu toko dengan satu kasir menghasilkan beban yang sangat kecil. Setiap komponen tambahan menambah satu hal yang bisa rusak pada pukul tujuh pagi saat toko baru buka, dan tidak satu pun dari daftar itu menyelesaikan masalah yang benar-benar kita punya.
