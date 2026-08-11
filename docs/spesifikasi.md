# Spesifikasi Induk: Sistem Informasi Manajemen Toko

- **Tanggal:** 2026-08-07
- **Status:** Disetujui, menjadi acuan implementasi
- **Jenis usaha:** Toko kelontong / minimarket yang **sudah beroperasi**
- **Tujuan ganda:** dipakai sungguhan di toko **dan** menjadi karya portofolio

---

## 1. Masalah

Toko sudah berjalan, tetapi seluruh pencatatan masih manual. Akibatnya:

- Stok tidak diketahui secara pasti sampai barang habis di rak.
- Laba tidak bisa dihitung, karena harga modal tiap barang tidak tercatat.
- Hutang ke pemasok hanya diingat, tidak dilacak.
- Pemilik tidak bisa memantau toko tanpa berada di tempat.

Sistem ini menutup keempat lubang itu tanpa menghentikan operasional toko selama masa peralihan.

## 2. Batasan yang membentuk seluruh rancangan

| Batasan | Asal | Dampak rancangan |
|---|---|---|
| Kasir tidak boleh berhenti saat internet putus | Internet toko sering terganggu | POS wajib bisa jalan offline, sehingga perlu replika katalog dan antrean kiriman |
| Bisa dibuka dari desktop **dan** HP, akhirnya dari mana saja | Pemilik ingin memantau dari luar toko | Aplikasi web responsif di server internet, bukan aplikasi desktop |
| Belum ada scanner, printer, atau laci uang | Toko masih manual | v1 wajib lengkap hanya dengan keyboard; perangkat keras bersifat tambahan |
| Seluruh perkakas gratis atau open source | Permintaan pemilik proyek | Lihat [ADR-0007](adr/0007-lapisan-gratis-dan-portabilitas.md) |
| Satu barang dijual dalam beberapa satuan, ada barang curah | Kenyataan toko kelontong | Tabel satuan bertingkat dan jumlah berangka pecahan |
| Pemilik proyek ingin belajar Python | Tujuan portofolio | Seluruh logika bisnis di Python (FastAPI) |

## 3. Lingkup v1

**Termasuk.** Keempatnya wajib, karena toko sudah beroperasi dan tidak bisa memakai sistem separuh jadi:

1. Kasir (POS): transaksi, sesi kas, retur, struk
2. Katalog dan stok: produk, satuan bertingkat, buku besar stok, opname, impor CSV
3. Pembelian dan pemasok: faktur, penerimaan barang, HPP, hutang
4. Laporan dan dashboard: omzet, laba kotor, persediaan, produk terlaris

**Tidak termasuk v1.** Ditunda, bukan dibuang:

- Lebih dari satu cabang toko
- Pelanggan tetap, kasbon pelanggan, program loyalitas
- Pembayaran digital terintegrasi (QRIS otomatis); v1 hanya mencatat metode bayar
- Aplikasi ponsel asli (native), karena PWA sudah cukup
- Integrasi perangkat keras, dirancang agar bisa ditambahkan dan dikerjakan di M8

## 4. Keputusan kunci

Ringkasan. Alasan lengkap ada di masing-masing ADR.

| # | Keputusan | Alasan singkat |
|---|---|---|
| [0001](adr/0001-spa-bukan-render-server.md) | Aplikasi satu halaman (SPA), bukan render di server | Halaman yang dirender server butuh server, persis yang hilang saat internet mati |
| [0002](adr/0002-fastapi-bukan-django.md) | FastAPI, bukan Django | Tampilan dipegang React, sehingga kekuatan Django tak terpakai; OpenAPI membangkitkan tipe TS otomatis |
| [0003](adr/0003-hpp-rata-rata-bergerak.md) | HPP rata-rata bergerak, bukan FIFO | FIFO menuntut pelacakan per lapisan, berlebihan untuk kelontong |
| [0004](adr/0004-offline-hanya-untuk-menjual.md) | Offline hanya untuk menjual | Penjualan bersifat tambah-saja, sehingga seluruh kategori masalah konflik data hilang |
| [0005](adr/0005-satuan-bertingkat.md) | Satuan bertingkat dan jumlah pecahan | Satu mekanisme menyelesaikan "jual per dus" dan "barang curah" sekaligus |
| [0006](adr/0006-stok-boleh-minus.md) | Stok boleh minus dengan peringatan | Menolak penjualan barang yang jelas ada di tangan pembeli akan membuat sistem ditinggalkan |
| [0007](adr/0007-lapisan-gratis-dan-portabilitas.md) | Lapisan gratis, dijaga tetap bisa dipindah | Tanpa biaya, tanpa terkunci penyedia |
| [0008](adr/0008-istilah-domain-bahasa-indonesia.md) | Istilah domain berbahasa Indonesia di kode dan basis data | Kode berbicara dengan bahasa yang sama seperti pemilik toko |
| [0009](adr/0009-postgresql-tersemat-tanpa-docker.md) | PostgreSQL tersemat, tanpa Docker | Pengembangan tanpa memasang apa pun ke sistem |

## 5. Bentuk sistem

```
┌────────────────────────┐        ┌──────────────────────┐
│  frontend/  (browser)  │        │  backend/  (Python)  │
│  React + TypeScript    │◄──────►│  FastAPI             │
│  PWA, responsif        │  HTTPS │  SQLAlchemy + Alembic│
│                        │  JSON  │                      │
│  IndexedDB:            │        │  Seluruh aturan      │
│   • salinan katalog    │        │  bisnis dihitung     │
│   • antrean penjualan  │        │  di sini             │
└────────────────────────┘        └──────────┬───────────┘
                                             │
                                    ┌────────▼─────────┐
                                    │   PostgreSQL     │
                                    │   sumber         │
                                    │   kebenaran      │
                                    └──────────────────┘
```

Kontrak antara keduanya berasal dari OpenAPI yang dibangkitkan FastAPI, lalu diterjemahkan menjadi tipe TypeScript. **Satu sumber kebenaran, ditulis di Python.**

## 6. Enam aturan bisnis yang tidak boleh dilanggar

1. **Buku besar stok adalah sumber kebenaran.** Kolom `stok` di produk hanya salinan cepat. Kalau berselisih, buku besar yang menang.
2. **HPP memakai rata-rata bergerak**, diperbarui hanya saat barang **diterima**.
3. **Baris nota menyimpan salinan harga dan HPP saat itu.** Laba historis harus tetap sama meski harga hari ini berubah.
4. **Stok boleh minus**, dicatat dan diperingatkan, dibereskan lewat opname.
5. **Nomor nota dibuat di perangkat** (`YYYYMMDD-K1-0007`), bukan menunggu server.
6. **Setiap penjualan membawa `uuid_klien`**; server menolak duplikat. Pengiriman ulang selalu aman.

Uang selalu bilangan bulat rupiah, dengan **satu pengecualian**: HPP disimpan berdesimal (`NUMERIC(14,4)`), karena ia tarif turunan yang dikalikan faktor satuan, bukan jumlah yang dibayarkan. Jumlah barang selalu `Decimal`, tidak pernah `float`.

## 7. Bab-bab detail

| Bab | Isi |
|---|---|
| [01 Kebutuhan](perancangan/01-kebutuhan.md) | Pengguna, kebutuhan fungsional dan non-fungsional, kriteria keberhasilan |
| [02 Arsitektur](perancangan/02-arsitektur.md) | Komponen, stack, struktur repo, penempatan |
| [03 Model Data](perancangan/03-model-data.md) | ERD, kamus data, aturan integritas |
| [04 Alur Kerja](perancangan/04-alur-kerja.md) | Alur tiap modul, langkah demi langkah |
| [05 Sinkronisasi Offline](perancangan/05-sinkronisasi-offline.md) | Replika katalog, antrean, idempotensi, kegagalan |
| [06 Antarmuka](perancangan/06-antarmuka.md) | Peta layar, wireframe, prinsip tampilan |
| [07 Kontrak API](perancangan/07-kontrak-api.md) | Daftar endpoint, bentuk permintaan dan jawaban |
| [08 Keamanan dan Peran](perancangan/08-keamanan-dan-peran.md) | Otentikasi, hak akses, sesi offline |
| [09 Penanganan Error](perancangan/09-penanganan-error.md) | Kegagalan yang diperkirakan dan tanggapannya |
| [10 Strategi Pengujian](perancangan/10-strategi-pengujian.md) | Apa yang diuji, di lapisan mana |
| [11 Rilis Bertahap](perancangan/11-rilis-bertahap.md) | M0 sampai M8, urutan dan alasannya |

## 8. Kriteria keberhasilan

Rancangan ini dianggap berhasil kalau, tiga bulan setelah M2:

- Kasir memakai sistem untuk **setiap** transaksi, bukan sebagian.
- Pemilik bisa menjawab "berapa laba bulan lalu?" tanpa menghitung manual.
- Selisih stok fisik terhadap catatan sistem saat opname bisa dijelaskan asal-usulnya lewat kartu stok.
- Tidak pernah ada transaksi yang hilang atau tercatat ganda.

## 9. Risiko yang diterima secara sadar

| Risiko | Peredam | Sisa risiko |
|---|---|---|
| Data browser dibersihkan saat antrean belum terkirim | Minta penyimpanan permanen, peringatan keras, struk cetak jadi bukti | Nyata, tidak hilang sepenuhnya |
| Aturan lapisan gratis berubah | Tanpa fungsi khusus vendor, sehingga pindah penyedia tidak menuntut tulis ulang; cadangan harian | Perlu tindakan manual saat terjadi |
| Kasir kembali ke cara manual karena sistem terasa lambat | Alur keyboard-first, pencarian lokal, "tambah cepat" saat transaksi | Perlu pendampingan di minggu pertama |
| Dua bahasa (Python dan TypeScript) memberatkan proses belajar | Pembagian tugas bersih, sehingga jarang menyentuh keduanya dalam satu tugas | Melekat pada pilihan arsitektur |
