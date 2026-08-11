# ADR-0006: Stok boleh minus

- **Tanggal:** 2026-08-07
- **Status:** Diterima

## Konteks

Apa yang harus dilakukan sistem ketika kasir menjual barang yang menurut catatan stoknya sudah nol, padahal barangnya jelas ada di tangan pembeli?

## Keputusan

**Penjualan diterima.** Stok menjadi negatif, mutasi tetap dicatat, peringatan ditampilkan, dan produk itu muncul di laporan "stok minus" untuk dibereskan lewat opname atau penyesuaian.

## Alasan

Stok nol pada catatan hampir tidak pernah berarti barangnya tidak ada. Yang lebih sering terjadi: barang belum pernah dicatat masuk, jumlah penerimaan salah ketik, atau produknya baru saja ditambahkan lewat "tambah cepat" di tengah antrean.

Menolak penjualan dalam keadaan itu berarti sistem memberi tahu kasir bahwa kenyataan di depan matanya salah. Kasir tidak akan berdebat. Ia akan berhenti memakai sistem, kembali ke nota tulis tangan, dan seluruh data toko ikut hilang bersamanya.

Angka minus juga bukan kerugian informasi. Justru sebaliknya: ia **penanda yang jujur dan otomatis** bahwa ada barang masuk yang belum tercatat. Stok yang dipaksa berhenti di nol menyembunyikan persoalan itu.

## Alternatif yang ditolak

**Menolak penjualan bila stok tidak cukup.** Benar secara sistem, salah secara toko.

**Menahan di nol tanpa mencatat kekurangannya.** Menyembunyikan besarnya masalah. Setelah dibereskan, tidak ada yang tahu berapa banyak yang sempat terlewat.

**Membuat penyesuaian otomatis diam-diam.** Membuat buku besar berbohong, dan menghapus jejak yang justru paling dibutuhkan saat menelusuri selisih.

## Konsekuensi

- Nilai persediaan bisa terhitung negatif untuk produk tertentu. Diterima, dan tetap ditampilkan apa adanya di laporan.
- Perhitungan HPP menangani stok negatif secara khusus: bila `stok_lama ≤ 0`, HPP baru langsung sama dengan harga beli, merata-ratakan terhadap stok negatif menghasilkan angka yang tidak berarti ([ADR-0003](0003-hpp-rata-rata-bergerak.md)).
- Laporan "stok minus" menjadi bagian rutin kerja pemilik, bukan daftar kelainan.
- Pengaturan `peringatan_stok_minus` bisa dimatikan bila peringatannya mulai mengganggu, tetapi **pencatatannya tidak pernah bisa dimatikan**.
