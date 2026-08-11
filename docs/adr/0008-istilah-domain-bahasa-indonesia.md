# ADR-0008 — Istilah domain memakai bahasa Indonesia

- **Tanggal:** 2026-08-07
- **Status:** Diterima

## Konteks

Sistem ini melayani toko Indonesia dan dipakai orang yang berbicara bahasa Indonesia. Penamaan tabel, fungsi, dan endpoint perlu ditetapkan sekali, di awal, sebelum ada kode.

## Keputusan

**Istilah domain memakai bahasa Indonesia** — di nama tabel, kolom, fungsi layanan, endpoint, dan berkas: `produk`, `penjualan`, `mutasi_stok`, `hpp`, `pemasok`, `sesi_kas`.

**Istilah teknis tetap bahasa Inggris**, mengikuti kelaziman perkakasnya: kata kunci bahasa pemrograman (`async def`, `SELECT`), nama pustaka dan fungsinya (`useState`, `Depends`), serta nama berkas yang ditentukan kerangka (`main.py`, `package.json`).

Batasnya: **kalau pemilik toko bisa mengucapkannya, tulis dalam bahasa Indonesia.** Kolom `id` tetap `id` karena itu istilah teknis; kolom waktu memakai `dibuat_pada`, `diubah_pada`, dan `waktu_transaksi`, bukan `created_at` — karena "waktu transaksi" adalah hal yang benar-benar dibicarakan di toko.

## Alasan

Kode yang memakai istilah yang sama dengan penggunanya menghapus satu lapis penerjemahan yang tidak perlu. Saat pemilik toko berkata "stoknya minus", ada tabel bernama `mutasi_stok` dan kolom bernama `stok` — bukan `inventory_movements` dan `quantity_on_hand` yang harus dipetakan di kepala setiap kali.

Istilah dagang Indonesia juga tidak selalu punya padanan Inggris yang tepat. **HPP** bukan persis *cost of goods sold*; **opname** bukan persis *stocktake*; **sesi kas** bukan persis *shift*. Menerjemahkannya justru menghilangkan ketepatan yang dimiliki istilah aslinya.

## Alternatif yang ditolak

**Seluruhnya bahasa Inggris.** Lebih lazim di proyek perangkat lunak dan lebih mudah dibaca pengembang asing. Ditolak karena pengguna dan pemilik proyek berbahasa Indonesia, dan biaya penerjemahan terus-menerus ditanggung setiap hari oleh orang yang benar-benar memakai sistem ini.

**Campuran tanpa aturan.** Yang paling sering terjadi bila tidak diputuskan di awal: `produk` bersanding dengan `sales_items`. Membingungkan tanpa memberi keuntungan apa pun.

## Konsekuensi

- Pengembang berbahasa Inggris butuh waktu menyesuaikan. Diredam oleh daftar istilah di [README perancangan](../perancangan/README.md).
- Nama endpoint berbahasa Indonesia (`/api/v1/penjualan`) bersanding dengan kata kerja HTTP berbahasa Inggris (`POST`). Ini wajar dan lazim — kata kerjanya milik protokol, kata bendanya milik domain.
- Pesan kesalahan sudah berbahasa Indonesia sejak dari server, sehingga antarmuka menampilkannya apa adanya tanpa lapisan penerjemahan.
- Untuk portofolio, keputusan ini perlu dijelaskan — dan penjelasannya justru menunjukkan pertimbangan yang matang, bukan kelalaian.
