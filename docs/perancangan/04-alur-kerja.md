# 04. Alur Kerja

Setiap alur ditulis sebagai langkah yang bisa ditelusuri, karena alur inilah yang nanti diterjemahkan langsung menjadi uji ujung-ke-ujung di [bab 10](10-strategi-pengujian.md).

## 4.1 Kasir — satu hari kerja

```
buka sesi kas  →  [ transaksi  ×  N ]  →  tutup sesi kas
```

### Membuka sesi kas (KAS-01)

1. Kasir masuk ke sistem.
2. Bila belum ada sesi terbuka atas namanya, sistem meminta **modal awal laci**.
3. Sesi tercatat dengan waktu buka. Layar kasir baru bisa dipakai setelah ini.

Tanpa sesi, kas fisik tidak bisa dicocokkan di akhir hari — jadi langkah ini tidak bisa dilewati.

### Melayani satu transaksi (KAS-02 s.d. KAS-10, KAS-13, KAS-15)

```
     ┌─ fokus di kolom cari ─────────────────────────────┐
     │                                                    │
     ▼                                                    │
 ketik / pindai ──► cocokkan ──► pilih satuan ──► keranjang ┘
                     │           (bila perlu)
                     ▼
              tidak ketemu ──► "tambah cepat" (STK-05)
```

**Urutan pencocokan pencarian**, berhenti pada kecocokan pertama:

1. **Barcode persis** pada `satuan_produk` → produk **dan** satuannya langsung tertentu, tidak ada pertanyaan lanjutan.
2. **Kode produk persis**.
3. **Nama mengandung kata kunci**, diurutkan berdasarkan seberapa sering produk itu terjual belakangan — barang yang laris muncul lebih dulu.

Pencarian dijalankan atas salinan katalog di perangkat. Inilah yang membuatnya seketika dan tetap hidup saat internet mati.

**Dua jalan untuk setiap tindakan.** Pintasan papan ketik memakai F-key (`F2` ubah jumlah, `F3` hapus baris, `F4` diskon nota, `F6` gantung, `F9` bayar, `Esc` batal), dan **setiap tindakan itu juga punya tombol di layar** — sehingga alur yang sama bisa diselesaikan dengan sentuhan di tablet atau HP ([bab 06 §6.3](06-antarmuka.md#63-layar-kasir)). Di laptop, F-key menuntut Fn-lock disetel saat pemasangan; syarat itu tercatat di [bab 11 §11.4](11-rilis-bertahap.md#114-peralihan-tanpa-menghentikan-toko).

**Pemilihan satuan.** Bila produk punya lebih dari satu satuan dan bukan hasil pindaian barcode, kasir memilih satuan lebih dulu. Bila hanya ada satu satuan, langkah ini dilewati diam-diam.

**Jumlah.** Nilai awal `1`. Untuk barang curah, kasir mengetik angka pecahan (`1,5`). Sistem menerima koma maupun titik sebagai pemisah desimal — pengguna Indonesia mengetik koma, papan ketik angka mengeluarkan titik, dan memaksanya konsisten cuma akan memperlambat kasir.

**Perhitungan tiap baris:**

```
jumlah_dasar = jumlah × faktor
subtotal     = bulatkan(harga_satuan × jumlah) − diskon
```

Pembulatan dilakukan sekali, di tingkat baris.

**Pembayaran (F9).**

- Tunai: kasir mengetik uang diterima; kembalian dihitung. Tersedia tombol pecahan cepat (Rp5.000 / 10.000 / 20.000 / 50.000 / 100.000 dan "uang pas").
- Transfer / QRIS: hanya dicatat metodenya. v1 tidak terhubung ke penyedia pembayaran mana pun.
- Bila `pembulatan_nota` diatur ke Rp100 atau Rp500, total dibulatkan dan selisihnya tersimpan di kolom `pembulatan` — bukan disembunyikan ke dalam diskon.

**Penyimpanan transaksi.** Nota selalu ditulis ke penyimpanan lokal lebih dulu, lengkap dengan `uuid_klien` dan `nomor_nota` yang dibuat di perangkat. Barulah pengiriman ke server diusahakan. Urutan ini penting: kalau pengiriman yang didahulukan, transaksi bisa hilang ketika jaringan putus di tengah jalan.

**Struk tidak menjadi bagian dari alur menyelesaikan transaksi.** Toko belum punya printer, jadi setelah pembayaran dikonfirmasi layar langsung menampilkan kembalian dan siap menerima transaksi berikutnya. Tombol **Cetak struk** tersedia untuk dipakai bila printer ada, memakai lembar gaya khusus lebar 58 mm dan 80 mm.

Bila pengaturan `cetak_otomatis` dinyalakan — dilakukan saat printer dibeli di M8 — dialog cetak muncul sendiri setelah setiap transaksi. Nota lama selalu bisa dicetak ulang dari daftar penjualan.

### Transaksi tergantung (KAS-06)

Kasir menggantung keranjang yang sedang berjalan, melayani pembeli lain, lalu memanggilnya kembali. Keranjang tergantung disimpan lokal dan tidak pernah dikirim ke server — ia belum menjadi penjualan.

### Retur (KAS-11)

1. Kasir mencari nota lama berdasarkan nomor atau tanggal.
2. Sistem menolak bila nota lebih tua dari `batas_hari_retur`.
3. Kasir menandai baris yang dikembalikan beserta jumlahnya.
4. Sistem memeriksa jumlah retur ≤ sisa baris asal.
5. Terbentuk `retur_penjualan` + mutasi stok bertipe `retur_penjualan` (bertanda positif), dan status nota asal berubah menjadi `sebagian_diretur` atau `diretur_penuh`.

**Nota asal tidak pernah diubah atau dihapus.** Koreksi selalu berupa catatan baru — itu yang membuat riwayat tetap bisa dipercaya.

Retur hanya bisa dilakukan saat online, karena membutuhkan nota asal yang mungkin tidak ada di perangkat ini.

### Menutup sesi kas (KAS-12)

1. Sistem menghitung `kas_sistem = modal_awal + penjualan tunai − retur tunai`.
2. Kasir menghitung uang di laci dan mengetikkan `kas_fisik`.
3. `selisih = kas_fisik − kas_sistem` ditampilkan.
4. Bila selisih bukan nol, **catatan wajib diisi**.
5. Sesi ditutup.

Sistem tidak pernah "membetulkan" selisih. Selisih adalah kenyataan yang perlu dilihat, bukan angka yang perlu dirapikan.

**Penutupan sesi menuntut antrean kosong.** Bila masih ada penjualan menunggu kirim, sesi tidak boleh ditutup — kas sistem belum lengkap dan hasil pencocokannya pasti menyesatkan.

## 4.2 Katalog & stok

### Pengisian awal (STK-04)

Karena toko belum punya data digital sama sekali, jalur ini menentukan apakah sistem terpakai atau tidak.

1. Pemilik mengunduh berkas CSV contoh berisi kepala kolom yang benar.
2. Mengunggah berkas isian.
3. Sistem menampilkan **pratinjau**: berapa baris akan masuk, berapa gagal, dan **tiap kegagalan menyebut nomor baris beserta alasannya** — bukan sekadar "impor gagal".
4. Pemilik memperbaiki berkas lalu mengulang dari langkah 2, atau melanjutkan hanya dengan baris yang sah — **berkas yang sama dikirim ulang** dan diperiksa ulang dari nol, karena pratinjau tidak menyimpan apa pun di server.
5. Baris yang masuk membuat produk, satuan dasarnya, dan bila kolom stok awal terisi, satu mutasi bertipe `stok_awal`.

Impor bersifat **semua-atau-tidak per baris**, tidak pernah separuh produk terbentuk.

### Tambah cepat saat transaksi (STK-05)

Kasir menemukan barang yang belum terdaftar sementara pembeli menunggu. Ia mengisi **nama dan harga saja**; produk terbentuk dengan kode otomatis, satuan dasar `pcs`, stok 0, dan penanda `perlu_dilengkapi`. Transaksi lanjut tanpa jeda.

Daftar "perlu dilengkapi" muncul di dashboard pemilik untuk dirapikan belakangan.

**Saat offline, produk ini belum punya `id` dari server.** Perangkat membuatkan `uuid_klien` untuknya dan menyimpannya lokal, lalu baris nota merujuk produk itu lewat UUID tersebut, bukan lewat `produk_id`. Server membuat produknya saat menerima nota, memakai UUID itu sebagai kunci idempotensi — sehingga barang yang sama, yang ditambahkan kilat sekali lalu terjual di lima nota berbeda, tetap menghasilkan **satu** produk. Rinciannya di [bab 07 §7.6](07-kontrak-api.md#76-penjualan).

Ini satu-satunya jalan penulisan katalog yang diizinkan saat offline, dan ia diizinkan justru karena ia bagian dari penjualan — bukan pengelolaan katalog.

Stok produk seperti ini akan langsung minus — dan itu memang tujuannya. Angka minus adalah pengingat yang jujur bahwa barang ini belum pernah dicatat masuk.

### Penyesuaian manual (STK-06)

Untuk barang rusak, hilang, atau kedaluwarsa. Kasir/pemilik memilih produk, mengisi jumlah bertanda, dan **alasan yang wajib diisi**. Terbentuk satu mutasi bertipe `penyesuaian`.

Kolom alasan yang boleh kosong akan selalu kosong. Enam bulan kemudian tidak ada yang ingat kenapa stok gula berkurang tujuh.

### Opname (STK-07, STK-08)

1. Pemilik membuat sesi opname, memilih seluruh produk atau satu kategori.
2. Sistem **membekukan `stok_sistem`** tiap baris pada saat pembuatan.
3. Pemilik keliling rak sambil memegang HP, mengisi `stok_fisik` per baris. Sesi boleh ditinggal dan dilanjutkan nanti — statusnya masih `draft`.
4. Selisih ditampilkan, diurutkan dari yang terbesar.
5. Saat diposting, tiap baris berselisih menghasilkan satu mutasi bertipe `opname`, dan stok produk menjadi sama dengan hitungan fisik.

Pembekuan di langkah 2 itulah yang membuat opname jujur: kalau `stok_sistem` dibaca ulang saat posting, penjualan yang terjadi selama penghitungan akan terhapus diam-diam.

## 4.3 Pembelian

### Menerima barang (BEL-02 s.d. BEL-05)

```
draft ──────────────────────────────► diterima
  │                                       │
  │ boleh diubah bebas                    │ stok bertambah
  │ tidak menyentuh stok                  │ HPP dihitung ulang
  │                                       │ tidak bisa diubah lagi
```

1. Pemilik membuat faktur: pemasok, nomor faktur, tanggal, jatuh tempo.
2. Menambah baris: produk, **satuan** (boleh `dus`), jumlah, harga beli per satuan itu.
3. Sistem menghitung `harga_beli_dasar = harga_beli ÷ faktor` dan `jumlah_dasar = jumlah × faktor`.
4. Selama berstatus `draft`, faktur bebas diubah dan **tidak menyentuh stok sama sekali**.
5. Saat ditandai **diterima**, dalam satu transaksi basis data: kunci baris produk, hitung HPP baru, tulis mutasi bertipe `pembelian`, perbarui stok, kunci faktur dari perubahan.

Memisahkan "memesan" dari "menerima" adalah cara paling langsung mencegah stok sistem berbeda dari rak. Faktur yang sudah diterima tidak bisa diubah; koreksinya lewat retur pembelian atau penyesuaian.

### Saran harga jual (BEL-05)

Bila harga beli naik dibanding penerimaan sebelumnya, sistem menampilkan saran harga jual yang mempertahankan margin lama:

```
margin_lama  = (harga_jual_sekarang − hpp_lama) ÷ hpp_lama
harga_saran  = bulatkan_ke_atas( hpp_baru × (1 + margin_lama) , 100 )
```

Ini **hanya saran**. Pemilik menyetujui, mengubah, atau mengabaikannya. Harga jual adalah keputusan dagang — dipengaruhi harga tetangga, kebiasaan pembeli, dan angka yang enak diucapkan — bukan hasil rumus.

### Hutang (BEL-06, BEL-07)

Faktur dengan jatuh tempo masuk daftar hutang. Pelunasan bisa dicicil; tiap cicilan menambah `dibayar` dan memperbarui `status_bayar`. Faktur yang mendekati atau melewati jatuh tempo muncul di dashboard pemilik.

## 4.4 Laporan

Semua laporan dihitung di server, memakai `waktu_transaksi` (waktu kejadian di perangkat), **bukan** `waktu_diterima`. Penjualan yang dibuat offline hari Selasa tetap masuk laporan Selasa meski baru sampai Rabu pagi.

| Laporan | Rumus inti |
|---|---|
| Omzet | `Σ penjualan.total` dalam rentang |
| Laba kotor | `Σ (item.subtotal − item.jumlah_dasar × item.hpp_saat_itu)`, dibulatkan sekali di akhir |
| Nilai persediaan | `Σ (produk.stok × produk.hpp)` |
| Produk terlaris | urut berdasarkan `Σ jumlah_dasar` atau `Σ subtotal` |
| Kartu stok | seluruh `mutasi_stok` satu produk beserta rujukannya |
| Stok minus | produk dengan `stok < 0` |
| Rekap sesi kas | sesi berikut selisihnya |

Laba kotor memakai `hpp_saat_itu` yang tersimpan di baris nota, **bukan** HPP hari ini. Karena itu laporan bulan lalu yang dibuka hari ini memberi angka yang sama persis dengan yang dibuka bulan lalu.

Setiap laporan bisa diekspor ke CSV (LAP-07).
