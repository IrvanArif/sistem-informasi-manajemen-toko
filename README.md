# Sistem Informasi Manajemen Toko

Sistem kasir dan manajemen stok untuk toko kelontong yang **sudah beroperasi**. Dirancang agar kasir tetap bisa berjualan ketika internet toko mati, dan pemilik tetap bisa memantau dari HP di mana saja.

> **Status: perancangan.** Belum ada kode. Dokumen perancangan sudah lengkap dan menjadi acuan implementasi.

## Masalah yang diselesaikan

Toko berjalan sepenuhnya dengan catatan manual. Akibatnya stok baru diketahui saat barang habis di rak, laba tidak bisa dihitung karena harga modal tidak tercatat, dan hutang ke pemasok hanya diingat.

## Bentuk sistem

```
React + TypeScript (PWA)  ──HTTPS/JSON──►  Python + FastAPI  ──►  PostgreSQL
 IndexedDB: katalog + antrean               seluruh aturan bisnis
```

| Bagian | Perkakas |
|---|---|
| Server | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, `uv` |
| Basis data | PostgreSQL |
| Antarmuka | React 19, TypeScript, Vite, Tailwind, shadcn/ui, Dexie |
| Pengujian | pytest, Hypothesis, pgserver, Vitest, Playwright |
| Penempatan | Cloudflare Pages + Render + Neon (lapisan gratis) |

Seluruhnya gratis atau open source: MIT, Apache, ISC, PSF, atau PostgreSQL License.

## Empat hal yang membuat rancangan ini tidak biasa

**Kasir tetap jalan tanpa internet.** Katalog disalin ke perangkat, penjualan masuk antrean lokal, dan terkirim sendiri saat koneksi pulih. Setiap nota membawa kunci idempotensi, sehingga pengiriman ulang tidak pernah menggandakan omzet.

**Satuan bertingkat dan barang curah lewat satu mekanisme.** Indomie per bungkus atau per dus, beras per kilogram dengan angka pecahan. Semuanya diselesaikan oleh faktor konversi terhadap satuan dasar: jual satu dus, stok berkurang empat puluh bungkus.

**Buku besar stok, bukan sekadar kolom angka.** Setiap perubahan stok menulis satu baris yang tidak pernah diubah atau dihapus. Pertanyaan "kenapa stok gula kurang tiga?" selalu punya jawaban.

**Uang tidak pernah disimpan sebagai bilangan pecahan biner.** Rupiah sebagai bilangan bulat, jumlah barang sebagai `Decimal`. Satu-satunya pengecualian adalah HPP, dan alasannya tertulis.

## Dokumen perancangan

Mulai dari **[spesifikasi induk](docs/spesifikasi.md)**, yang memuat masalah, batasan, lingkup, dan keputusan kunci.

- **[Bab-bab perancangan](docs/perancangan/)**: kebutuhan, arsitektur, model data, alur kerja, sinkronisasi, antarmuka, API, keamanan, penanganan error, pengujian, rilis
- **[Catatan keputusan arsitektur](docs/adr/)**: sembilan keputusan berikut alternatif yang ditolak dan alasannya
- **[Kebijakan repositori](docs/kebijakan-repositori.md)**: apa yang boleh dan tidak boleh diunggah, dan apa yang dilakukan bila rahasia telanjur bocor

## Rencana rilis

| | Tahap | Selesai berarti |
|---|---|---|
| M0 | Fondasi | Aplikasi bisa diakses, pemilik bisa membuat akun kasir, CI hijau |
| M1 | Katalog | Seluruh barang toko masuk sistem |
| **M2** | **Kasir inti** | **Toko mulai memakai sistem setiap hari** |
| **M3** | **Offline** | **Kasir tetap menjual saat internet mati** |
| M4 | Kasir lengkap | Retur, transaksi tergantung, non-tunai, cetak |
| M5 | Pembelian | Harga modal nyata, sehingga laba bisa dihitung |
| M6 | Stok lanjutan | Selisih stok bisa dijelaskan |
| M7 | Laporan | Pemilik memantau dari HP |
| M8 | Perangkat keras | Scanner, printer, laci uang |

M2 sengaja dibuat kecil. Retur, transaksi tergantung, dan pembayaran non-tunai digeser ke M4 supaya **M3 tiba lebih cepat**, karena internet toko sering putus.

Rincian dan alasan urutannya di [bab 11](docs/perancangan/11-rilis-bertahap.md).
