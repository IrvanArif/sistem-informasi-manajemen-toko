# 01. Kebutuhan

## 1.1 Pengguna

Hanya ada dua peran. Menambah peran ketiga sebelum ada orangnya adalah menebak-nebak.

### Pemilik

Menjalankan toko, memutuskan harga, membeli barang dari pemasok, dan ingin tahu apakah toko untung. Sering berada di luar toko dan memantau lewat HP.

Yang dia butuhkan dari sistem, berurut dari yang paling mendesak:

1. Berapa omzet dan laba hari ini / bulan ini
2. Barang apa yang hampir habis dan perlu dibeli
3. Berapa hutang ke pemasok dan kapan jatuh tempo
4. Apakah kas fisik cocok dengan catatan sistem

### Kasir

Melayani pembeli di depan mesin. Ukuran keberhasilan baginya cuma satu: **antrean tidak menumpuk.** Kalau sistem memperlambatnya walau sedikit, dia akan kembali ke kalkulator dan nota tulis tangan, dan seluruh data toko ikut hilang bersamanya.

Karena itu kasir tidak boleh dipaksa: menunggu jaringan, memakai mouse, atau berhenti karena barang belum terdaftar.

> Di banyak toko kecil, pemilik dan kasir adalah orang yang sama. Sistem harus tetap masuk akal dalam kondisi itu: satu orang yang berganti peran, bukan dua akun yang saling menunggu.

## 1.2 Kebutuhan fungsional

Diberi kode agar bisa dirujuk dari rencana implementasi dan dari uji.

### Kasir (KAS)

| Kode | Kebutuhan |
|---|---|
| KAS-01 | Kasir membuka sesi kas dengan mengisi modal awal laci |
| KAS-02 | Mencari barang dengan mengetik barcode, kode, atau nama; hasil muncul seketika dari data lokal |
| KAS-03 | Menambah barang ke keranjang, memilih satuan bila produk punya lebih dari satu |
| KAS-04 | Mengisi jumlah berangka pecahan untuk barang curah (mis. `1,5` kg) |
| KAS-05 | Memberi diskon per baris maupun per nota, dalam rupiah atau persen |
| KAS-06 | Menggantung transaksi dan melayani pembeli lain, lalu melanjutkannya |
| KAS-07 | Menerima pembayaran tunai dengan hitung kembalian otomatis dan tombol pecahan cepat |
| KAS-08 | Mencatat metode bayar non-tunai (transfer / QRIS) tanpa integrasi otomatis |
| KAS-09 | Menerapkan pembulatan total nota ke Rp100 atau Rp500 sesuai pengaturan |
| KAS-10 | Menyelesaikan transaksi **tanpa** langkah cetak; struk dicetak lewat tombol opsional atau otomatis bila pengaturan `cetak_otomatis` menyala |
| KAS-11 | Melakukan retur atas nota lama dalam batas waktu yang diatur; stok kembali lewat mutasi bertipe `retur` |
| KAS-12 | Menutup sesi kas: bandingkan kas sistem dengan kas fisik, catat selisih dan alasannya |
| KAS-13 | Menyelesaikan seluruh alur di atas **tanpa mouse** (pintasan F-key) |
| KAS-15 | Menyelesaikan seluruh alur di atas **tanpa papan ketik**, lewat tombol sentuh. Tidak ada tindakan yang hanya bisa dicapai lewat pintasan |
| KAS-14 | Menjual saat internet mati; transaksi masuk antrean dan terkirim sendiri |

### Pengguna & Akses (AKS)

Toko dijalankan sendiri oleh pemilik saat ini, tetapi pegawai akan direkrut dalam waktu dekat. Karena itu pembagian peran dibangun **sejak M0**, sebab menambahkannya setelah data transaksi menumpuk jauh lebih mahal daripada menyediakannya sekarang.

| Kode | Kebutuhan |
|---|---|
| AKS-01 | Pemilik membuat akun pengguna baru beserta perannya (`pemilik` atau `kasir`) |
| AKS-02 | Pemilik menonaktifkan akun; akun **tidak pernah dihapus** agar jejak transaksinya tetap utuh |
| AKS-03 | Pemilik mengatur ulang sandi pengguna lain |
| AKS-04 | Setiap pengguna mengubah sandinya sendiri |
| AKS-05 | Sistem menolak tindakan yang membuat toko kehilangan seluruh akun `pemilik` aktif |

### Katalog & Stok (STK)

| Kode | Kebutuhan |
|---|---|
| STK-01 | Mengelola kategori |
| STK-02 | Mengelola produk: kode, nama, kategori, satuan dasar, stok minimum, status aktif |
| STK-03 | Mengelola satuan tiap produk: nama, faktor, harga jual, barcode |
| STK-04 | Mengimpor produk dari CSV dengan pratinjau dan laporan baris gagal yang menyebut nomor baris dan alasannya |
| STK-05 | Menambah produk secara kilat di tengah transaksi (nama + harga saja), ditandai "perlu dilengkapi" |
| STK-06 | Menyesuaikan stok secara manual dengan **alasan wajib** |
| STK-07 | Membuat sesi opname, mengisi stok fisik per kategori, memposting selisih sebagai mutasi |
| STK-08 | Mengisi opname dengan nyaman lewat layar HP |
| STK-09 | Melihat kartu stok satu produk: seluruh mutasi berikut rujukannya |
| STK-10 | Melihat daftar barang di bawah stok minimum |
| STK-11 | Melihat daftar barang berstok minus untuk dibereskan |

### Pembelian & Pemasok (BEL)

| Kode | Kebutuhan |
|---|---|
| BEL-01 | Mengelola pemasok |
| BEL-02 | Membuat faktur pembelian berstatus draft |
| BEL-03 | Mencatat item pembelian dalam satuan apa pun, dikonversi ke satuan dasar |
| BEL-04 | Menandai faktur "diterima". **Hanya saat inilah** stok bertambah dan HPP dihitung ulang |
| BEL-05 | Melihat saran harga jual baru saat harga beli naik; sistem tidak pernah mengubahnya sendiri |
| BEL-06 | Melacak hutang: total, jatuh tempo, sisa |
| BEL-07 | Mencatat pelunasan hutang secara bertahap (cicil) |

### Laporan (LAP)

| Kode | Kebutuhan |
|---|---|
| LAP-01 | Dashboard ringkas yang terbaca di layar HP |
| LAP-02 | Laporan penjualan per periode, per produk, per kategori, per kasir |
| LAP-03 | Laba kotor dari `Σ(harga jual − HPP saat transaksi)` |
| LAP-04 | Nilai persediaan dari `Σ(stok × HPP)` |
| LAP-05 | Produk terlaris berdasarkan jumlah maupun nilai penjualan |
| LAP-06 | Rekap sesi kas berikut selisihnya |
| LAP-07 | Ekspor setiap laporan ke CSV |

## 1.3 Kebutuhan non-fungsional

| Kode | Kebutuhan | Angka |
|---|---|---|
| NF-01 | Pencarian produk terasa seketika | < 100 ms untuk 5.000 produk, dari data lokal |
| NF-02 | Transaksi 10 item selesai cepat | < 30 detik termasuk pembayaran |
| NF-03 | Aplikasi terbuka saat internet mati | < 3 detik |
| NF-04 | Ukuran katalog yang didukung | Sampai 5.000 produk tanpa penurunan terasa |
| NF-05 | Data toko tidak boleh hilang | Cadangan otomatis harian + uji pemulihan berkala |
| NF-06 | Seluruh antarmuka berbahasa Indonesia | Termasuk pesan kesalahan |
| NF-07 | **Dapat dioperasikan penuh** di HP, tablet, maupun desktop | Sejak lebar 360 px, termasuk layar kasir |
| NF-08 | Tanpa biaya lisensi | Seluruh komponen gratis atau open source |
| NF-09 | Bisa dipindah penyedia | Tanpa fungsi khusus vendor; penempatan lewat `Dockerfile` yang dibangun di sisi penyedia |

## 1.4 Yang sengaja dikorbankan

Rancangan yang jujur menyebut apa yang dia relakan.

- **Ketepatan HPP.** Rata-rata bergerak sedikit kurang tepat dibanding FIFO. Ditukar dengan model data yang jauh lebih sederhana. → [ADR-0003](../adr/0003-hpp-rata-rata-bergerak.md)
- **Kelengkapan fitur offline.** Hanya menjual yang jalan offline. Ditukar dengan hilangnya seluruh kelas masalah konflik data. → [ADR-0004](../adr/0004-offline-hanya-untuk-menjual.md)
- **Kepastian stok.** Stok boleh minus. Ditukar dengan sistem yang tidak pernah menghalangi penjualan nyata. → [ADR-0006](../adr/0006-stok-boleh-minus.md)
- **Kemewahan tampilan.** Layar kasir mengutamakan kecepatan dan keterbacaan, bukan keindahan. Animasi dan transisi tidak dipakai di jalur transaksi.

## 1.5 Kriteria keberhasilan

Diukur tiga bulan setelah M2 (kasir inti) dipakai:

1. Setiap transaksi tercatat di sistem, bukan sebagian.
2. Pemilik menjawab "berapa laba bulan lalu?" tanpa hitung manual.
3. Setiap selisih opname bisa dilacak asal-usulnya lewat kartu stok.
4. Nol transaksi hilang, nol transaksi ganda.
