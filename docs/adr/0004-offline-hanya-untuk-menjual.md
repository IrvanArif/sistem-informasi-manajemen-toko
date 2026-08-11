# ADR-0004 — Offline hanya untuk menjual

- **Tanggal:** 2026-08-07
- **Status:** Diterima

## Konteks

Kasir harus tetap bekerja saat internet mati. Pertanyaannya: **seberapa banyak** sistem yang perlu berjalan offline?

## Keputusan

Hanya **penjualan** yang berjalan offline. Menambah dan mengubah produk, menerima barang dari pemasok, melakukan retur, memposting opname, dan membuka laporan semuanya menuntut internet.

## Alasan

Penjualan bersifat **tambah-saja**. Tidak pernah ada dua pihak yang mengubah baris yang sama, sehingga tidak ada konflik yang perlu diputuskan mesin sinkronisasi. Yang tersisa cuma satu pertanyaan — "apakah pesan ini sudah sampai?" — dan itu punya jawaban baku: kunci idempotensi.

Begitu perubahan katalog diizinkan offline, kita berhadapan dengan dua perangkat yang mengubah harga produk yang sama lalu harus memilih pemenang. Tidak ada pilihan yang benar di situ, hanya pilihan yang salahnya berbeda-beda. Untuk toko dengan satu kasir, kerumitan itu tidak dibayar oleh manfaat apa pun.

Batasan ini juga cocok dengan kenyataan kerja: mengurus katalog, menerima barang, dan membuka laporan tidak pernah dilakukan sambil pembeli mengantre.

## Alternatif yang ditolak

**Sinkronisasi dua arah penuh** (CRDT atau "penulis terakhir menang"). Menyelesaikan masalah yang tidak dimiliki toko ini, dengan harga berupa bagian tersulit di seluruh sistem.

**Tanpa offline sama sekali.** Toko berhenti berjualan setiap kali internet terganggu. Tidak bisa diterima.

**Server di komputer toko.** Kasir jadi paling kebal gangguan, tetapi "diakses dari mana saja" berubah dari bonus menjadi pekerjaan besar tersendiri, dan komputer toko harus selalu menyala dan terurus.

## Konsekuensi

- Mesin sinkronisasi bisa dijelaskan dalam satu halaman ([bab 05](../perancangan/05-sinkronisasi-offline.md)).
- Saat offline, produk baru hanya bisa ditambahkan lewat "tambah cepat" yang tersimpan lokal, dan baru menjadi produk sungguhan saat tersinkron.
- Retur tidak bisa dilakukan offline, karena membutuhkan nota asal yang mungkin tidak ada di perangkat.
- Bila kelak ada kasir kedua, keputusan ini tetap berlaku tanpa perubahan — dua perangkat yang sama-sama hanya menambah penjualan tetap tidak berkonflik.
