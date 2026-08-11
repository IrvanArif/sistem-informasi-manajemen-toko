# 08. Keamanan & Peran

## 8.1 Dua peran

Saat ini pemilik menjalankan toko sendirian, tetapi pegawai akan direkrut dalam waktu dekat. Pembagian peran karena itu dibangun **sejak M0**, bukan ditunda sampai pegawainya datang, menyisipkan pemisahan hak akses setelah data transaksi menumpuk jauh lebih mahal, dan biasanya dikerjakan terburu-buru justru saat orang baru sudah berdiri di depan mesin kasir.

| Tindakan | Pemilik | Kasir |
|---|---|---|
| Membuka & menutup sesi kas | Ya | Ya |
| Melayani transaksi penjualan | Ya | Ya |
| Menggantung & melanjutkan transaksi | Ya | Ya |
| Melakukan retur | Ya | Ya |
| Menambah produk kilat saat transaksi | Ya | Ya |
| Mengisi stok fisik saat opname | Ya | Ya |
| **Melihat HPP dan laba** | Ya | Tidak |
| **Mengubah harga jual** | Ya | Tidak |
| Mengelola produk, satuan, kategori | Ya | Tidak |
| Mengimpor CSV | Ya | Tidak |
| Menyesuaikan stok manual | Ya | Tidak |
| Memposting opname | Ya | Tidak |
| Mengelola pemasok & pembelian | Ya | Tidak |
| Menerima barang | Ya | Tidak |
| Melihat laporan | Ya | Tidak |
| Mengubah sandi sendiri | Ya | Ya |
| Mengelola akun pengguna (buat, nonaktifkan, atur ulang sandi) | Ya | Tidak |
| Mengelola pengaturan toko | Ya | Tidak |

Kasir tetap bisa melihat rekap sesi kasnya sendiri. Itu pekerjaannya, dan dia yang bertanggung jawab atas selisihnya. Angka penjualan hariannya pun sudah terlihat di sana, jadi menutup laporan penuh tidak menghalangi pekerjaan apa pun.

### Tiga batas yang paling menentukan

**Harga modal.** Informasi dagang yang tidak perlu diketahui pegawai. Karena itu `hpp` disaring di server dan **tidak pernah ikut terkirim** ke perangkat kasir, bukan dikirim lalu disembunyikan di layar.

**Harga jual.** Keputusan pemilik. Kasir yang bisa mengubahnya berarti tidak ada harga yang benar-benar tetap.

**Posting opname.** Ini yang paling sering disalahpahami sebagai birokrasi. Kasir boleh *mengisi* hitungan stok fisik. Itu memang pekerjaan lapangan, tetapi hanya pemilik yang boleh **memposting**nya menjadi mutasi.

> Alasannya bukan soal kepercayaan, melainkan struktur: orang yang bisa **menjual** sekaligus **menyesuaikan stok agar cocok** dapat mengambil barang tanpa meninggalkan jejak apa pun. Selisih yang seharusnya muncul di laporan justru terhapus oleh tindakannya sendiri.
>
> Selama kedua wewenang itu dipegang orang berbeda, setiap kehilangan barang akan muncul sebagai selisih yang harus dijelaskan. Merepotkan, dan kerepotan itulah gunanya.

Pembagian ini tetap masuk akal saat pemilik dan kasir adalah orang yang sama. Ia masuk sebagai pemilik untuk mengurus katalog, lalu bekerja di layar kasir seperti biasa.

### Mengelola akun pengguna

Karena pegawai akan segera direkrut, pemilik butuh cara membuat akunnya (AKS-01 s.d. AKS-05, endpoint di [bab 07 §7.2](07-kontrak-api.md#72-otentikasi)). Tiga penjagaan menyertainya:

| Penjagaan | Alasan |
|---|---|
| Akun **dinonaktifkan, tidak pernah dihapus** | Nota dan mutasi lama merujuk penggunanya; menghapus akun memutus jejak audit |
| Sistem menolak tindakan yang menyisakan **nol pemilik aktif** | Toko yang terkunci dari sistemnya sendiri tidak punya jalan pulih tanpa akses basis data |
| Pengguna **tidak bisa mengubah perannya sendiri** | Menaikkan peran selalu tindakan orang lain, meski pelakunya pemilik |

Akun yang masih punya sesi kas terbuka juga tidak bisa dinonaktifkan, kas yang belum dicocokkan tidak boleh kehilangan penanggung jawabnya.

### Penegakan

Hak akses ditegakkan di **server**, sebagai dependensi FastAPI pada tiap rute. Antarmuka juga menyembunyikan menu yang tidak relevan, tetapi itu semata kenyamanan.

> **Menyembunyikan tombol bukan pengendalian akses.** Setiap endpoint memeriksa peran sendiri, tanpa mengandalkan apa pun yang dikirim perangkat.

Selain itu, endpoint yang mengembalikan data produk memfilter kolom `hpp` berdasarkan peran, bukan sekadar tidak menampilkannya di layar. Data yang tidak pernah dikirim tidak bisa dibaca dari alat pengembang browser.

## 8.2 Otentikasi

**Sandi** di-hash dengan **Argon2id** (`argon2-cffi`, lisensi MIT).

**Token:** JWT akses berumur 15 menit + token segar berumur 30 hari dengan **rotasi**. Setiap pemakaian token segar menerbitkan yang baru dan mencabut yang lama; bila token yang sudah dicabut dipakai lagi, seluruh sesi pengguna itu dicabut, pertanda token dicuri.

**Pembatasan percobaan masuk:** 5 kegagalan dalam 15 menit per nama pengguna, dan terpisah per alamat IP. Kegagalan dicatat.

### Kenapa token disimpan di JavaScript, bukan cookie httpOnly

Cookie `httpOnly` lebih aman terhadap serangan XSS, dan itu pilihan yang lebih baik, **tetapi tidak bisa dipakai di sini.**

Tampilan berada di `*.pages.dev` sementara API di `*.onrender.com`. Bagi browser itu dua situs berbeda, sehingga cookienya menjadi cookie pihak ketiga, jenis yang sedang dibatasi habis-habisan oleh browser modern. Membangun otentikasi di atas mekanisme yang sedang dihapus adalah utang yang jatuh temponya sudah diumumkan.

Menyatukan keduanya di bawah satu domain akan menyelesaikan ini, tetapi domain sendiri berbiaya, dan proyek ini dibatasi tanpa biaya ([ADR-0007](../adr/0007-lapisan-gratis-dan-portabilitas.md)).

Jadi token disimpan di penyimpanan lokal perangkat, dengan peredam:

- **Content-Security-Policy ketat** tanpa `unsafe-inline` dan `unsafe-eval`
- Tidak ada `dangerouslySetInnerHTML` di seluruh kode
- Umur token akses pendek (15 menit)
- Rotasi token segar dengan deteksi pemakaian ulang
- Pemeriksaan kerentanan dependensi otomatis di CI

**Bila toko kelak memakai domain sendiri, pindahkan ke cookie `httpOnly` `SameSite=Lax`.** Ini dicatat sebagai utang teknis yang disengaja, bukan kelalaian.

## 8.3 Otentikasi saat offline

Selama offline, perangkat tidak memanggil API sama sekali, jadi tidak ada yang perlu diotentikasi saat itu. Yang berlaku:

1. Identitas kasir dan `sesi_kas_id` yang aktif tersimpan lokal saat masuk terakhir.
2. Penjualan yang dibuat offline mencatat identitas tersebut.
3. Saat koneksi pulih, antrean dikirim memakai token yang ada. Bila tokennya kedaluwarsa, sistem meminta masuk ulang lalu **melanjutkan antrean secara otomatis**, antrean tidak pernah dibuang karena sesi habis.
4. Server memeriksa bahwa kasir pengirim memang pemilik `sesi_kas_id` itu.

Tidak ada kunci layar berbasis PIN di v1. Komputer kasir berada di dalam toko dan pengamanannya bersifat fisik; menambahkan PIN berarti menjalankan pemeriksaan sandi di dalam browser tanpa server, pekerjaan yang tidak sebanding dengan manfaatnya di sini.

## 8.4 Pengamanan lain

| Bidang | Tindakan |
|---|---|
| Pengangkutan data | HTTPS wajib; HSTS menyala |
| CORS | Hanya asal frontend yang diizinkan, bukan `*` |
| Suntikan SQL | Seluruh kueri lewat SQLAlchemy berparameter; tidak ada perangkaian string |
| Validasi masukan | Pydantic di batas terluar; layanan tidak pernah menerima data mentah |
| Rahasia | Lewat variabel lingkungan; `.env` tidak pernah masuk repositori |
| Dependensi | `pip-audit` dan `npm audit` berjalan di CI |
| Unggahan CSV | Batas ukuran, hanya `text/csv`, diproses di memori tanpa disimpan |
| Jejak audit | `mutasi_stok` dan `penjualan` sudah menjadi jejak; ditambah catatan untuk kegagalan masuk dan perubahan harga jual |

## 8.5 Pencadangan

Data toko yang hilang tidak bisa dibeli kembali. Ini bukan pelengkap keamanan. Ini bagian utamanya.

- **Harian**, lewat GitHub Actions terjadwal: `pg_dump` seluruh basis data.
- **Terenkripsi** dengan `age` (lisensi BSD) memakai kunci publik; kunci pribadi tidak pernah menyentuh CI.
- **Disimpan** sebagai artefak GitHub Actions dengan masa simpan 90 hari, ditambah salinan bulanan yang diunduh pemilik ke penyimpanan miliknya sendiri.
- **Diuji pulih setiap tiga bulan** ke basis data sementara. Cadangan yang tidak pernah diuji pulih bukanlah cadangan. Itu asumsi.

Lapisan gratis Neon menyimpan riwayat perubahan 24 jam terakhir. Itu berguna untuk kekeliruan kecil, tetapi tidak melindungi dari layanannya sendiri menghilang. Karena itu cadangan disimpan di tempat yang berbeda dari basis datanya.
