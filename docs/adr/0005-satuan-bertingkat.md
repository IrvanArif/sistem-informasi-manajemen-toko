# ADR-0005: Satuan bertingkat dengan jumlah berdesimal

- **Tanggal:** 2026-08-07
- **Status:** Diterima

## Konteks

Toko menjual barang yang sama dalam beberapa satuan (Indomie per bungkus **dan** per dus, dari tumpukan yang sama), dan menjual barang curah yang ditimbang (beras per kilogram, bisa 1,5 kg).

## Keputusan

Satu tabel `satuan_produk` yang menyimpan nama satuan, **faktor** terhadap satuan dasar, harga jual, dan barcode. Stok selalu disimpan dalam satuan dasar sebagai `NUMERIC(14,3)`.

Barang curah adalah kasus khusus yang tidak memerlukan mekanisme terpisah: satuan dasarnya `kg` dengan faktor 1, dan jumlahnya kebetulan berdesimal.

## Alasan

Dua kebutuhan yang tampak berbeda, "jual per dus" dan "jual per kilo", ternyata dilayani satu mekanisme: **jumlah dalam satuan terpilih, dikalikan faktor, menjadi jumlah dalam satuan dasar.** Membangun dua sistem terpisah untuk keduanya berarti menulis dua kali dan salah dua kali.

Tanpa ini, "Indomie bungkus" dan "Indomie dus" harus menjadi dua produk berstok terpisah, dan setiap kali satu dus dibongkar ke rak, stoknya harus dipindahkan manual. Sistem akan berbohong sejak minggu pertama.

## Rincian penting

**Harga tiap satuan ditulis sendiri, bukan dihitung dari perkalian.** Satu dus Rp130.000, bukan 40 × Rp3.500 = Rp140.000, dan justru selisih itulah alasan pembeli mengambil per dus. Harga dus yang dihitung otomatis akan salah terus, lalu ditambal dengan diskon palsu yang mengotori laporan.

**Barcode menempel pada satuan, bukan pada produk.** Dus punya barcode sendiri, sehingga satu pindaian menentukan produk dan satuannya sekaligus.

**Jumlah tidak pernah `float`.** `NUMERIC(14,3)` di basis data, `Decimal` di Python, string di JSON. Dalam `float`, `0.1 + 0.2` menghasilkan `0.30000000000000004`; selisih sekecil itu menumpuk lintas ribuan transaksi dan muncul sebagai selisih stok yang tidak bisa dijelaskan siapa pun.

## Alternatif yang ditolak

**Satu satuan per produk.** Model data paling ramping, tetapi tidak sesuai kenyataan toko.

**Produk terpisah per satuan.** Tidak menuntut perubahan model, tetapi memindahkan pekerjaan ke manusia setiap kali kemasan dibongkar, dan pekerjaan manual yang berulang selalu terlewat.

**Jumlah sebagai bilangan bulat "gram".** Menghindari desimal, tetapi membuat setiap tampilan dan masukan harus dibagi seribu. Sumber kekeliruan yang tak berkesudahan.

## Konsekuensi

- Setiap penjualan, pembelian, dan opname melewati satu langkah konversi.
- Antarmuka kasir kadang perlu menanyakan satuan, dilewati diam-diam bila produk hanya punya satu, atau bila satuannya sudah tertentu dari barcode.
- Laporan selalu menyebut satuan dasar, supaya angkanya bisa dijumlahkan tanpa konversi berulang.
