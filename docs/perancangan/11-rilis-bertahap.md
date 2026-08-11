# 11. Rilis Bertahap

## 11.1 Prinsip urutan

Toko **sudah beroperasi**. Ia tidak bisa menunggu seluruh modul selesai sebelum memperoleh manfaat apa pun, dan tidak boleh berhenti berjualan selama peralihan.

Ada dua tuntutan yang saling menekan:

1. **Secepat mungkin sampai ke titik toko bisa memakainya setiap hari**. Itu M2.
2. **Internet toko sering putus**, sehingga kasir yang hanya jalan online akan langsung dianggap tidak bisa dipakai. Itu menuntut M3 tiba cepat pula.

Cara mendamaikannya bukan membesarkan M2 sampai memuat offline sekaligus, melainkan **mengecilkan M2**. Fitur kasir yang bisa menunggu digeser ke M4, sehingga M3 tiba lebih cepat secara kalender **dan** dibangun di atas alur yang sudah tidak berubah bentuk.

## 11.2 Tahapan

| Tahap | Isi | Selesai berarti |
|---|---|---|
| **M0** Fondasi | Repositori, PostgreSQL tersemat, skema & migrasi, otentikasi, **peran & pengelolaan akun pengguna**, alur CI | Aplikasi kosong berjalan di localhost, pemilik bisa membuat akun kasir, dan CI hijau |
| **M1** Katalog | Produk, kategori, satuan bertingkat, impor CSV, buku besar stok, stok awal | Seluruh barang toko sudah masuk sistem dengan stok awalnya |
| **M2** Kasir inti | Sesi kas, pencarian, keranjang, satuan & jumlah pecahan, diskon, **tambah cepat**, bayar tunai, tutup kasir | **Toko mulai memakai sistem setiap hari** |
| **M3** Offline | Service worker, salinan katalog, antrean, pengiriman latar, idempotensi, indikator status, tambah cepat saat offline | **Kasir tetap menjual saat internet mati** |
| **M4** Kasir lengkap | Retur, transaksi tergantung, pembayaran non-tunai, pembulatan nota, cetak struk | Alur kasir utuh sesuai [bab 04](04-alur-kerja.md) |
| **M5** Pembelian | Pemasok, faktur, penerimaan barang, HPP, hutang, saran harga | Harga modal akhirnya nyata, laba bisa dihitung |
| **M6** Stok lanjutan | Opname, penyesuaian, kartu stok, stok menipis, stok minus | Selisih stok bisa ditemukan dan dijelaskan |
| **M7** Laporan | Dashboard HP, penjualan, laba, persediaan, terlaris, rekap kas, ekspor CSV | Pemilik memantau toko dari HP di mana saja |
| **M8** Perangkat keras | Barcode scanner, printer thermal ESC/POS, laci uang | Alat baru tinggal dicolok |

**Apa yang sengaja tidak ada di M2**, dan bagaimana toko bertahan tanpanya selama beberapa minggu:

| Ditunda ke M4 | Cara bertahan sementara |
|---|---|
| Retur | Ditangani manual seperti sekarang, lalu stoknya dibetulkan lewat penyesuaian di M6, atau dicatat di buku sampai M4 tiba |
| Transaksi tergantung | Kasir menyelesaikan satu transaksi sebelum melayani berikutnya, seperti hari ini |
| Pembayaran non-tunai | Dicatat sebagai tunai dengan catatan; kolom `metode_bayar` sudah ada sejak M2 sehingga datanya tidak perlu dimigrasikan |
| Pembulatan nota | `pembulatan_nota` bernilai `0`. Harga kelontong umumnya sudah bulat, jadi totalnya pun bulat |
| Cetak struk | Printernya memang belum ada ([bab 06 §6.3](06-antarmuka.md#setelah-bayar-tanpa-langkah-cetak)) |

## 11.3 Alasan di balik urutannya

**Kenapa penempatan ke internet ditunda dari M0.** Semula M0 berakhir dengan menempatkan aplikasi ke internet, dengan alasan aplikasi kosong paling mudah dicari tahu penyebab kegagalannya. Atas keputusan pemilik proyek pada 2026-08-08, seluruh M0 dikerjakan di localhost lebih dulu agar pengembangannya lebih ringan.

Konsekuensinya perlu dilihat terbuka: kebutuhan "pemilik memantau dari HP di mana saja" belum terpenuhi sampai penempatan dikerjakan, dan makin lama ditunda makin banyak bagian yang ikut diperiksa saat penempatan pertama gagal. Batas yang disepakati: **paling lambat sebelum M3**, karena mesin sinkronisasi menuntut server yang benar-benar bisa dijangkau dari luar.

**Kenapa pembagian peran ada di M0, bukan ditunda.** Pegawai belum direkrut saat M0 dikerjakan, sehingga menundanya terasa masuk akal. Tetapi menyisipkan pemisahan hak akses setelah ada data transaksi berarti menyentuh ulang setiap endpoint yang sudah jadi, dan pekerjaan itu biasanya baru disadari mendesak ketika orang barunya sudah berdiri di depan mesin kasir. Membangunnya di awal, saat belum ada apa-apa yang bisa rusak, jauh lebih murah.

**Kenapa M1 sebelum M2.** Kasir tanpa katalog tidak bisa apa-apa. Dan karena data toko belum ada dalam bentuk digital sama sekali, pengisian awal adalah pekerjaan manusia berhari-hari yang bisa berjalan **bersamaan** dengan pembangunan M2.

**Kenapa M2 dikecilkan, bukan digabung dengan M3.** Ini keputusan yang paling menentukan di seluruh bab, jadi alasannya perlu terang.

Internet toko sering putus, sehingga kasir yang hanya jalan online akan langsung dianggap tidak bisa dipakai. Godaan pertamanya adalah menggabungkan M2 dan M3 supaya kasir lahir sudah lengkap sekaligus tahan offline. Godaan itu ditolak karena dua sebab:

**Pertama, gabungan itu justru membuat offline datang lebih lambat.** Tahap gabungan berisi seluruh alur kasir *ditambah* seluruh mesin sinkronisasi, tahap terbesar di proyek ini. Toko tidak memperoleh apa pun sampai keduanya selesai. Dengan mengecilkan M2 sebagai gantinya, toko mulai memakai sistem lebih awal **dan** offline tiba lebih cepat secara kalender.

**Kedua, mesin sinkronisasi tidak boleh dibangun di atas alur yang masih berubah bentuk.** Antrean penjualan menyimpan bentuk nota apa adanya; setiap perubahan pada susunan keranjang, diskon, atau pembayaran menuntut penanganan data lama yang sudah terlanjur mengantre. Membiarkan alur kasir mengeras dulu selama M2, dipakai sungguhan, ketahuan janggalnya, diperbaiki, membuat M3 dibangun sekali saja.

Jeda antara M2 dan M3 memang tetap ada, dan selama itu kasir kembali ke nota tulis tangan saat internet mati. Tapi jedanya sependek mungkin, dan tidak ada yang menjadi lebih buruk daripada hari ini.

**Kenapa retur ditunda ke M4, bukan ikut M2.** Retur menyentuh nota yang sudah tersimpan dan menuntut nota asalnya ada di perangkat, hal yang tidak dijamin saat offline ([bab 04 §4.1](04-alur-kerja.md#41-kasir-satu-hari-kerja)). Menaruhnya sebelum M3 berarti membangun aturannya dua kali: sekali untuk dunia yang selalu online, sekali lagi setelah antrean masuk. Setelah M3, aturannya ditulis sekali dengan batas offline yang sudah jelas.

**Kenapa M5 sebelum M7.** Laporan laba tanpa HPP yang nyata cuma menghasilkan angka yang tampak meyakinkan tapi salah, dan angka salah yang terlihat rapi lebih berbahaya daripada tidak ada angka sama sekali. HPP baru terisi benar setelah pembelian dicatat.

**Kenapa M8 terakhir.** Alatnya belum dibeli. Dan karena alur kasir dirancang keyboard-first sejak awal, scanner USB akan langsung bekerja tanpa penyesuaian apa pun, pekerjaan tersisa cuma printer dan laci uang.

## 11.4 Peralihan tanpa menghentikan toko

Selama M1 sampai M3, toko tetap berjualan seperti biasa.

1. **Selama M1**, pemilik mengisi katalog di luar jam sibuk. Stok awal dimasukkan lewat opname pertama, bukan tebakan.
2. **Sebelum M2 dipakai**, siapkan mesin kasirnya: pasang aplikasi sebagai PWA, jalankan sinkron katalog pertama, dan **setel Fn-lock bila kasirnya laptop**, supaya `F9` tidak menuntut `Fn+F9` ratusan kali sehari ([bab 06 §6.3](06-antarmuka.md#tombol-pintas-dan-syarat-fn-lock)). Periksa ulang setelan ini setiap kali laptopnya diganti atau BIOS-nya direset.
3. **Awal M2**, sistem dipakai berdampingan dengan cara lama selama beberapa hari: setiap transaksi dicatat di keduanya, lalu totalnya dibandingkan di akhir hari. Selisih apa pun berarti ada yang belum benar, dan lebih baik ketahuan sekarang.
4. **Setelah dua hari berturut-turut totalnya cocok**, cara lama dihentikan.
5. **Nota tulis tangan tetap disiapkan** sebagai jalan keluar darurat sampai M3 selesai. Karena internet toko sering putus, ini akan benar-benar terpakai, bukan formalitas. Nota darurat dimasukkan ke sistem di hari yang sama, dengan `waktu_transaksi` disetel ke waktu kejadian sebenarnya supaya laporannya tidak bergeser hari.

Langkah 3 terasa merepotkan dan memang begitu. Tapi mengganti pencatatan uang sebuah usaha yang sedang berjalan tanpa masa berdampingan adalah cara paling langsung kehilangan kepercayaan pada sistem baru di hari pertama.

**Setelah M3 selesai**, nota tulis tangan disimpan, bukan dibuang. Ia tetap jadi jalan keluar terakhir bila perangkat kasirnya sendiri yang bermasalah, bukan internetnya.

## 11.5 Yang ditunda ke luar v1

Ditulis agar tercatat sebagai keputusan, bukan kelupaan:

| Ditunda | Kapan layak ditinjau ulang |
|---|---|
| Cabang toko kedua | Saat cabang benar-benar ada, konsolidasi stok mengubah banyak hal |
| Pelanggan tetap & kasbon | Saat pemilik mulai mencatat hutang pembeli di buku terpisah |
| QRIS terintegrasi | Saat porsi pembayaran non-tunai cukup besar sehingga pencatatan manual terasa berat |
| Aplikasi ponsel asli | Kemungkinan tidak pernah, PWA sudah menutupi kebutuhannya |
| Beberapa kasir sekaligus | Saat antrean pembeli menuntut mesin kedua |
| Harga bertingkat grosir | Saat toko mulai melayani pembeli besar secara rutin |
