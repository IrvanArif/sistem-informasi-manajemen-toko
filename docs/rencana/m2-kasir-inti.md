# Rencana Implementasi M2: Kasir Inti

**Tujuan:** Toko bisa memakai sistem untuk setiap transaksi, setiap hari.

**Lingkup sengaja sempit.** Retur, transaksi tergantung, pembayaran non-tunai, pembulatan nota, dan cetak struk **tidak** dikerjakan di sini. Semuanya digeser ke M4 agar M3 (offline) tiba lebih cepat, karena internet toko sering putus ([bab 11 §11.3](../perancangan/11-rilis-bertahap.md)).

**Acuan:** [Bab 03 Model Data](../perancangan/03-model-data.md) · [Bab 04 §4.1](../perancangan/04-alur-kerja.md) · [Bab 06 §6.3](../perancangan/06-antarmuka.md)

## Batasan yang mulai mengikat

| # | Batasan | Sumber |
|---|---|---|
| N1 | **Nomor nota dibuat di perangkat**, `YYYYMMDD-K1-0007`, bukan menunggu server. | Bab 03 aturan #5 |
| N2 | **Setiap penjualan membawa `uuid_klien`.** Server menolak duplikat dan menjawab data yang sudah tersimpan. | Bab 03 aturan #6 |
| N3 | **Baris nota menyimpan salinan** nama, harga, faktor, dan HPP saat itu. Laba historis tidak boleh berubah saat harga hari ini berubah. | Bab 03 aturan #3 |
| N4 | **Server menghitung ulang** subtotal dan total, lalu menolak bila berbeda dari yang dikirim. Yang diterima apa adanya hanya `harga_satuan`. | Bab 07 §7.6 |
| N5 | **HPP diambil pada saat `waktu_transaksi`**, ditelusuri dari buku besar, bukan HPP sekarang. | Bab 05 §5.5 |
| N6 | **Sesi kas wajib terbuka** sebelum transaksi. Selisih kas tanpa catatan ditolak. | KAS-01, KAS-12 |

## Tugas

### Tugas 1: Model sesi kas, penjualan, item penjualan
`app/model/kas.py`, `app/model/penjualan.py`, migrasi, uji model.

Kunci: `uuid_klien` dan `nomor_nota` keduanya `UNIQUE`. `waktu_transaksi` dan `waktu_diterima` disimpan terpisah, karena nota offline baru sampai berjam-jam kemudian dan laporan harus memakai waktu kejadian.

### Tugas 2: Layanan sesi kas
`buka_sesi`, `sesi_aktif`, `tutup_sesi`, `hitung_kas_sistem`.

Satu sesi terbuka per kasir. Selisih tanpa catatan ditolak. Sistem tidak pernah membetulkan selisih: ia kenyataan yang perlu dilihat.

### Tugas 3: Layanan penjualan
`catat_penjualan(sesi, data, kasir) -> Penjualan` yang idempoten terhadap `uuid_klien`, menghitung ulang total, menelusuri HPP pada waktu transaksi, memotong stok lewat `catat_mutasi`, dan menerima `produk_baru` untuk tambah cepat offline.

### Tugas 4: Endpoint kasir
`POST /penjualan`, `GET /penjualan`, `POST /sesi-kas`, `GET /sesi-kas/aktif`, `POST /sesi-kas/{id}/tutup`.

### Tugas 5 sampai 7: Layar kasir
Keranjang keyboard-first dengan F-key dan tombol sentuh, dialog bayar tunai berikut tombol pecahan cepat, layar buka dan tutup sesi kas.

### Tugas 8: Pemeriksaan M2 ujung-ke-ujung
Satu hari kasir utuh pada basis data kosong: buka sesi, tiga transaksi termasuk barang curah dan penjualan per dus, tutup sesi dengan selisih, dan pastikan buku besar tetap selaras.
