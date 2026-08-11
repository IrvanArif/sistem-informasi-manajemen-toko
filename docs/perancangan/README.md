# Dokumen Perancangan Sistem Informasi Manajemen Toko

Kumpulan dokumen ini adalah **rancangan sebelum implementasi**. Belum ada kode yang ditulis.

## Cara membaca

Mulai dari [Spec Induk](../spesifikasi.md), di sana ada masalah, batasan, lingkup, dan seluruh keputusan kunci. Bab-bab di folder ini adalah detailnya.

Kalau kamu ingin tahu **kenapa** sesuatu diputuskan begitu, jawabannya ada di [catatan keputusan arsitektur (ADR)](../adr/), bukan di bab teknis. Bab teknis menjelaskan *apa*; ADR menjelaskan *kenapa* dan *apa alternatif yang ditolak*.

## Daftar bab

| Bab | Isi | Status |
|---|---|---|
| [01, Kebutuhan](01-kebutuhan.md) | Pengguna, kebutuhan fungsional & non-fungsional | Sudah didiskusikan |
| [02, Arsitektur](02-arsitektur.md) | Komponen, stack, struktur repo, penempatan | Sudah didiskusikan |
| [03, Model Data](03-model-data.md) | ERD, kamus data, aturan integritas | Sudah didiskusikan |
| [04, Alur Kerja](04-alur-kerja.md) | Alur tiap modul, langkah demi langkah | Sudah didiskusikan |
| [05, Sinkronisasi Offline](05-sinkronisasi-offline.md) | Replika, antrean, idempotensi, kegagalan | Sudah didiskusikan |
| [06, Antarmuka](06-antarmuka.md) | Peta layar, wireframe, prinsip tampilan | Sudah didiskusikan |
| [07, Kontrak API](07-kontrak-api.md) | Daftar endpoint dan bentuk datanya | Sudah didiskusikan |
| [08, Keamanan & Peran](08-keamanan-dan-peran.md) | Otentikasi, hak akses, sesi offline | Sudah didiskusikan |
| [09, Penanganan Error](09-penanganan-error.md) | Kegagalan yang diperkirakan dan tanggapannya | Sudah didiskusikan |
| [10, Strategi Pengujian](10-strategi-pengujian.md) | Apa yang diuji, di lapisan mana | Sudah didiskusikan |
| [11, Rilis Bertahap](11-rilis-bertahap.md) | M0–M8, urutan dan alasannya | Sudah didiskusikan |

Bab bertanda ditulis berdasarkan keputusan yang sudah disepakati di bab 01–05, tetapi **isinya sendiri belum ditinjau**. Periksa bab-bab itu lebih teliti.

## Istilah

Istilah domain memakai bahasa Indonesia secara konsisten, di dokumen, di nama tabel, dan di nama fungsi. Alasannya di [ADR-0008](../adr/0008-istilah-domain-bahasa-indonesia.md).

| Istilah | Arti di sistem ini |
|---|---|
| **Satuan dasar** | Satuan terkecil tempat stok disimpan (bungkus, kg, botol) |
| **Faktor** | Berapa satuan dasar dalam satu satuan turunan (1 dus = 40 bungkus → faktor 40) |
| **HPP** | Harga Pokok Penjualan, harga modal rata-rata per satuan dasar |
| **Mutasi stok** | Satu baris catatan perubahan stok yang tidak pernah diubah atau dihapus |
| **Opname** | Penghitungan fisik stok untuk dicocokkan dengan catatan sistem |
| **Antrean / outbox** | Penjualan yang dibuat offline dan menunggu dikirim ke server |
| **Sesi kas** | Satu periode kerja kasir, dari isi modal awal sampai hitung kas penutup |
