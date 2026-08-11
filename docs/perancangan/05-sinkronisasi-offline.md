# 05. Sinkronisasi Offline

## 5.1 Prinsip: sesempit mungkin

**Yang boleh berjalan offline hanya menjual.** Mengelola katalog, menerima barang, melakukan retur, dan membuka laporan tetap menuntut internet.

Ada satu pengecualian sempit: **"tambah cepat" saat transaksi** (STK-05). Produk yang lahir dari situ ikut menumpang di dalam nota, dibedakan lewat `uuid_klien` miliknya sendiri, dan baru dibuat di server saat nota itu diterima. Pengecualian ini diizinkan justru karena ia bagian dari penjualan, kasir tidak sedang mengelola katalog, ia sedang melayani pembeli yang memegang barang tak dikenal.

Batasan ini menghapus seluruh kategori masalah sekaligus. Penjualan bersifat **tambah-saja**: tidak pernah ada dua pihak yang mengubah baris yang sama, sehingga tidak ada konflik yang perlu diputuskan mesin. Yang tersisa cuma satu pertanyaan teknis, "apakah pesan ini sudah sampai?", dan itu punya jawaban baku.

Kalau perubahan katalog juga diizinkan offline, kita akan berhadapan dengan dua perangkat yang mengubah harga produk yang sama, lalu harus memilih pemenang. Tidak ada pilihan yang benar di situ, hanya pilihan yang salahnya berbeda-beda. → [ADR-0004](../adr/0004-offline-hanya-untuk-menjual.md)

## 5.2 Tiga bagian bergerak

```
        SERVER                                   PERANGKAT KASIR
  ┌──────────────┐                        ┌──────────────────────────┐
  │  PostgreSQL  │                        │        IndexedDB         │
  │              │  ①  katalog turun      │  ┌────────────────────┐  │
  │  produk      │ ─────────────────────► │  │ salinan katalog    │  │
  │  satuan      │     (hanya yang        │  └────────────────────┘  │
  │              │      berubah)          │                          │
  │              │                        │  ┌────────────────────┐  │
  │  penjualan   │ ◄───────────────────── │  │ antrean penjualan  │  │
  │              │  ②  penjualan naik     │  └────────────────────┘  │
  └──────────────┘     (satu per satu)    └──────────────────────────┘
                                                      ▲
                                            ③ pengirim latar
                                              memantau status jaringan
```

## 5.3 Penyimpanan lokal

| Tabel IndexedDB | Isi |
|---|---|
| `produk` | `id`, `kode`, `nama`, `kategori_id`, `satuan_dasar`, `stok_perkiraan`, `aktif`, `uuid_klien` |
| `satuan` | `id`, `produk_id`, `nama`, `faktor`, `harga_jual`, `barcode`, `is_dasar` |
| `kategori` | `id`, `nama` |
| `antrean` | `uuid_klien` (kunci), `nomor_nota`, `muatan`, `status`, `percobaan`, `kesalahan_terakhir`, `dibuat_pada` |
| `keranjang_tergantung` | keranjang yang digantung; tidak pernah dikirim ke server |
| `meta` | `waktu_sinkron_terakhir`, `sesi_kas_aktif`, `kode_perangkat`, `selisih_jam` |

**Salinan katalog tidak memuat HPP.** Kasir tidak berhak melihat harga modal ([bab 08](08-keamanan-dan-peran.md)), dan data yang tidak pernah dikirim ke perangkat tidak bisa bocor dari perangkat.

`stok_perkiraan` adalah tebakan untuk ditampilkan saja. Stok yang sah dihitung server. Namanya sengaja mengandung kata "perkiraan" supaya tidak ada yang keliru memakainya sebagai kebenaran.

Produk hasil "tambah cepat" saat offline juga tinggal di tabel `produk` lokal, dengan `id` kosong dan `uuid_klien` terisi, sehingga ia langsung muncul di pencarian kasir untuk pembeli berikutnya, sebelum server tahu keberadaannya. Saat sinkron, `id` dari server mengisi baris yang sama.

## 5.4 Katalog turun

```
GET /sinkron/katalog?sejak=2026-08-07T02:15:00Z
```

Server mengembalikan hanya baris dengan `diubah_pada > sejak`, dibatasi per halaman, beserta `waktu_server`. Perangkat menyimpan `waktu_server` itu sebagai penanda sinkron berikutnya.

**Penandanya adalah waktu server, bukan waktu perangkat.** Jam komputer toko bisa meleset berhari-hari, dan penanda yang salah akan membuat perubahan katalog terlewat diam-diam.

Karena sistem ini tidak pernah menghapus data, produk dinonaktifkan lewat `aktif = false` ([bab 03 §3.3](03-model-data.md#33-aturan-integritas) aturan integritas #6), tidak ada daftar penghapusan yang perlu disinkronkan. Penonaktifan sampai sebagai perubahan biasa.

Sinkron katalog dijalankan saat aplikasi dibuka, setiap 15 menit selama online, dan setiap kali koneksi pulih.

## 5.5 Penjualan naik

### Urutan saat kasir menekan "Bayar"

```
1. buat uuid_klien + nomor_nota  ──► di perangkat, tidak menunggu siapa pun
2. tulis ke antrean IndexedDB    ──► WAJIB berhasil sebelum langkah 3
3. tampilkan struk               ──► kasir sudah bisa melayani pembeli berikutnya
4. usahakan kirim ke server      ──► boleh gagal, tidak apa-apa
```

Urutannya tidak boleh dibalik. Kalau pengiriman didahulukan, transaksi bisa lenyap saat jaringan putus tepat di tengah, dan uang sudah berpindah tangan.

### Pengiriman

Antrean dikirim **satu per satu, berurutan sesuai waktu pembuatan**. Berurutan bukan karena server menuntutnya, melainkan agar penelusuran masalah tetap masuk akal dan nomor nota terbaca berurutan di laporan.

Jeda antar percobaan menaik: **5 detik → 15 detik → 1 menit → 5 menit → 15 menit** (berhenti naik di situ). Pengiriman juga dipicu segera saat peristiwa `online` browser muncul.

### Idempotensi

`POST /penjualan` memakai `uuid_klien` sebagai kunci. Server memeriksa keberadaannya di dalam transaksi yang sama dengan penyimpanan, memanfaatkan batasan `UNIQUE`:

- **Belum ada** → simpan, potong stok, jawab `201`.
- **Sudah ada** → jawab `200` berikut data yang tersimpan sebelumnya. Tidak ada yang dipotong dua kali.

Inilah yang membuat pengiriman ulang selalu aman. Kalau jaringan putus tepat setelah server menyimpan tetapi sebelum jawabannya sampai, perangkat akan mengirim ulang, dan server cukup menjawab "sudah ada, ini datanya". **Tanpa ini, satu gangguan jaringan bisa menggandakan omzet.**

### Harga yang dikirim perangkat

Server menerima harga dari perangkat apa adanya, karena harga itulah yang tercetak di struk dan disepakati pembeli. Katalog di server mungkin sudah berubah sejak perangkat terakhir sinkron, tetapi mengubah nota agar cocok dengan harga baru berarti membuat catatan berbeda dari kenyataan.

Yang dilakukan server: **membandingkan** dengan harga katalog saat itu, dan menandai nota yang menyimpang lebih dari 20% untuk ditinjau pemilik. Menerima bukan berarti tidak mengawasi.

### Produk yang lahir bersama nota

Baris nota boleh merujuk produk lewat `produk_id` (produk yang sudah ada di salinan katalog) **atau** lewat `produk_baru` berisi `uuid_klien`, nama, dan harga (hasil "tambah cepat" saat offline). Server menangani keduanya dalam transaksi yang sama:

1. Untuk tiap `produk_baru`, cari produk ber-`uuid_klien` sama. Bila ada, pakai itu. Bila belum, buat produk `perlu_dilengkapi` beserta satuan dasarnya.
2. Baru kemudian baris nota disimpan dan stok dipotong.

Karena pencariannya memakai `uuid_klien` yang sama, satu barang yang ditambahkan kilat sekali lalu terjual di lima nota berbeda tetap menghasilkan **satu** produk, bukan lima produk kembar yang harus digabungkan manual belakangan.

### Penentuan HPP untuk nota offline

Server menetapkan `hpp_saat_itu` dari HPP produk **pada saat `waktu_transaksi`**, ditelusuri lewat mutasi stok terakhir sebelum waktu itu. Bila tidak ada, dipakai HPP berjalan.

Ini penting untuk nota yang baru sampai berjam-jam kemudian: bila di sela itu ada penerimaan barang yang mengubah HPP, memakai HPP sekarang akan membuat laba transaksi pagi dihitung dengan harga modal sore.

### Jam perangkat meleset

Setiap sinkron berhasil, perangkat membandingkan jamnya dengan waktu server dan menyimpan selisihnya. Bila selisih melebihi 5 menit, muncul peringatan, jam yang meleset merusak `waktu_transaksi`, dan itu merusak setiap laporan yang memakainya.

## 5.6 Status yang selalu terlihat

Bilah status di layar kasir tidak pernah kosong:

| Tampilan | Arti |
|---|---|
| **Hijau**, tersinkron | Antrean kosong, katalog mutakhir |
| **Kuning**, 3 transaksi menunggu** | Ada antrean, pengiriman sedang diusahakan |
| **Merah**, Offline** | Tidak ada koneksi; penjualan tetap bisa dilakukan |
| **1 transaksi gagal** | Ada yang ditolak server dan butuh tindakan manusia |

Kasir tidak boleh perlu menebak apakah pekerjaannya tersimpan.

## 5.7 Skenario kegagalan

| Skenario | Yang terjadi | Tanggapan sistem |
|---|---|---|
| Internet putus saat menyimpan | Nota tetap masuk antrean, struk tercetak | Indikator merah, penjualan lanjut |
| Putus setelah server simpan, sebelum jawaban tiba | Perangkat mengira gagal, mengirim ulang | Server mengenali `uuid_klien`, jawab `200`, tanpa duplikat |
| Server 5xx | Kegagalan sementara | Coba lagi dengan jeda menaik |
| Server 4xx (data tidak sah) | Kegagalan permanen | Tandai, hentikan percobaan, tampilkan alasan dan muatannya |
| Token kedaluwarsa (401) | Sesi habis | Minta masuk ulang, lalu antrean dilanjutkan otomatis |
| Antrean menumpuk (>50 atau tertua >24 jam) | Ada yang tidak beres | Peringatan mencolok, tetapi **penjualan tidak pernah dihalangi** |
| Data browser dibersihkan | Antrean hilang | Tidak bisa dipulihkan, lihat §5.8 |
| Katalog belum pernah tersinkron | Perangkat baru, belum siap | Layar kasir tidak bisa dibuka sebelum sinkron pertama |
| Tutup sesi kas saat antrean belum kosong | Kas sistem belum lengkap | Penutupan ditolak sampai antrean bersih |

Perhatikan pola yang berulang: **tidak ada kegagalan yang berujung pada "kasir tidak bisa menjual"**, kecuali perangkat memang belum pernah siap.

## 5.8 Batas yang diakui terus terang

Kalau data browser dibersihkan, pengguna membersihkan riwayat, browser dipasang ulang, browser menyingkirkan data karena ruang penyimpanan menipis, **penjualan yang masih menunggu akan hilang.**

Peredamnya berlapis:

1. Aplikasi meminta status penyimpanan permanen ke browser (`navigator.storage.persist()`), yang membuat browser tidak menyingkirkan datanya sendiri.
2. Peringatan mencolok begitu antrean menumpuk atau menua.
3. Aplikasi dipasang sebagai PWA, sehingga tidak ikut terhapus saat riwayat browser dibersihkan.
4. Struk cetak tetap menjadi bukti fisik yang bisa dimasukkan ulang secara manual.

Tapi peredam bukan jaminan. Ini harga yang dibayar untuk bisa berjualan tanpa internet, dan harga itu sepadan, kehilangan beberapa transaksi karena kejadian langka masih jauh lebih murah daripada berhenti berjualan setiap kali internet terganggu.

Kalau di kemudian hari risiko ini terasa terlalu besar, jalan keluarnya bukan menambal tambalan, melainkan pindah ke arsitektur lain, server di komputer toko, yang alternatifnya sudah dibahas di [ADR-0001](../adr/0001-spa-bukan-render-server.md).
