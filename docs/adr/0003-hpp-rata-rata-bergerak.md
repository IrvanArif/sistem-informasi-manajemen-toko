# ADR-0003: HPP memakai rata-rata bergerak, bukan FIFO

- **Tanggal:** 2026-08-07
- **Status:** Diterima

## Konteks

Laba kotor menuntut harga modal tiap barang. Harga beli berubah setiap kali barang datang, sehingga harus ada cara menetapkan modal satu barang yang terjual.

## Keputusan

**Rata-rata bergerak**, dihitung ulang setiap kali barang **diterima**:

```
hpp_baru = (stok_lama × hpp_lama + jumlah_masuk × harga_beli_dasar)
           ÷ (stok_lama + jumlah_masuk)
```

Bila `stok_lama` nol atau negatif, `hpp_baru = harga_beli_dasar`. Penjualan tidak pernah mengubah HPP.

HPP disimpan `NUMERIC(14,4)`, satu-satunya pengecualian terhadap aturan "uang selalu bilangan bulat rupiah", karena ia tarif turunan yang dikalikan faktor satuan, bukan jumlah yang dibayarkan.

## Alasan

FIFO memang lebih tepat secara akuntansi, tetapi menuntut pelacakan setiap lapisan pembelian: berapa sisa dari kiriman tanggal 3, berapa dari tanggal 17, dan dari lapisan mana barang yang barusan terjual diambil. Itu berarti satu tabel tambahan, penyusutan lapisan pada setiap penjualan, dan penanganan khusus untuk retur.

Untuk toko kelontong dengan barang yang harganya bergerak perlahan, ketelitian tambahan itu tidak mengubah keputusan apa pun yang diambil pemilik. Rata-rata bergerak adalah praktik lazim di ritel kecil dan cukup jujur.

## Alternatif yang ditolak

**FIFO.** Lebih tepat, jauh lebih rumit. Ditolak karena tidak ada keputusan dagang yang berubah karenanya.

**Harga beli terakhir.** Paling sederhana, tetapi satu kiriman mahal langsung membuat seluruh stok lama tampak bermodal tinggi, dan laba melonjak-lonjak tanpa alasan nyata.

**Tanpa HPP sama sekali.** Berarti tidak ada laporan laba, padahal itu kebutuhan pemilik nomor satu.

## Konsekuensi

- Laba per transaksi sedikit meleset dibanding FIFO; totalnya sepanjang waktu tetap benar.
- Nilai persediaan dihitung `Σ(stok × hpp)`, sederhana dan langsung.
- Barang yang terjual sebelum pernah dicatat masuk (lewat "tambah cepat") ber-HPP nol sampai penerimaan pertamanya. Labanya akan tampak terlalu besar sampai saat itu. Ini konsekuensi yang diterima, dan produk seperti itu ditandai `perlu_dilengkapi` agar cepat dibereskan.
