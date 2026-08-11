# 06. Antarmuka

## 6.1 Dua pengguna, dua prioritas yang berbeda

Sistem ini melayani dua orang dengan kebutuhan yang bertolak belakang, dan mencoba menyenangkan keduanya dengan satu tata letak akan mengecewakan keduanya.

| | Kasir | Pemilik |
|---|---|---|
| Perangkat | Layar lebar, keyboard | HP, satu tangan |
| Ukuran keberhasilan | Kecepatan per transaksi | Kejelasan angka |
| Sikap terhadap mouse | Menghambat | Wajar |
| Toleransi terhadap animasi | Nol | Wajar |

Karena itu **layar kasir dioptimalkan untuk desktop dan keyboard**, sedangkan **dashboard, laporan, dan opname dioptimalkan untuk HP**.

Tetapi "dioptimalkan untuk" tidak berarti "hanya jalan di". **Setiap layar wajib rapi dan bisa dioperasikan penuh dari 360 px ke atas**, tidak ada tombol yang terpotong, tidak ada tabel yang mendorong halaman melebar ke samping, tidak ada tindakan yang cuma bisa dicapai lewat papan ketik. Layar kasir di HP tetap bisa menyelesaikan transaksi; ia hanya tidak secepat di PC, dan memang tidak dirancang untuk itu.

## 6.2 Peta layar

```
Masuk
 ├── Kasir (peran: kasir, pemilik)
 │    ├── Buka sesi kas
 │    ├── Transaksi          ← layar utama
 │    ├── Transaksi tergantung
 │    ├── Retur
 │    └── Tutup sesi kas
 ├── Katalog (peran: pemilik)
 │    ├── Daftar produk
 │    ├── Ubah produk + satuannya
 │    ├── Impor CSV
 │    ├── Kategori
 │    └── Penyesuaian stok
 ├── Stok (peran: pemilik; isian opname juga oleh kasir)
 │    ├── Opname
 │    ├── Kartu stok per produk
 │    ├── Stok menipis
 │    └── Stok minus
 ├── Pembelian (peran: pemilik)
 │    ├── Daftar faktur
 │    ├── Faktur baru / terima barang
 │    ├── Pemasok
 │    └── Hutang & pelunasan
 ├── Laporan (peran: pemilik)
 │    └── Dashboard, penjualan, laba, persediaan, sesi kas
 └── Pengaturan (peran: pemilik)
      ├── Data toko, pembulatan, batas retur, cetak otomatis
      └── Pengguna, buat akun, ubah peran, nonaktifkan, atur ulang sandi
```

Satu layar tambahan berlaku untuk **semua peran**: **Ubah sandi sendiri**, dicapai dari menu akun. Kasir tidak punya hak apa pun di Pengaturan, tetapi sandinya tetap miliknya sendiri.

## 6.3 Layar kasir

```
┌──────────────────────────────────────────────────────────────────────┐
│ Toko Berkah   Kasir: Irvan   Sesi #12    hijau Tersinkron       12:04  │
├────────────────────────────────────────────┬─────────────────────────┤
│  Cari / pindai ▸ ______________________    │                         │
│                                            │        TOTAL            │
│  #  Nama            Satuan   Jml   Subtotal│                         │
│  1  Indomie Goreng  bungkus    3     10.500│      Rp 39.500          │
│  2  Beras Pandan    kg       1,5     21.000│                         │
│  3  Teh Botol       botol      2      8.000│  Item          6,5      │
│                                            │  Subtotal    39.500     │
│                                            │  Diskon           0     │
│                                            │  Pembulatan       0     │
│                                            │                         │
│                                            │  ┌───────────────────┐  │
│                                            │  │  F9  ·  B A Y A R │  │
│                                            │  └───────────────────┘  │
├────────────────────────────────────────────┴─────────────────────────┤
│ [F2 Ubah jml] [F3 Hapus] [F4 Diskon] [F6 Gantung] [Esc Batal]        │
└──────────────────────────────────────────────────────────────────────┘
```

Bilah bawah itu **tombol sungguhan yang bisa disentuh atau diklik**, bukan sekadar keterangan. Labelnya memuat pintasannya sekaligus, sehingga kasir yang memakai mouse hari ini akan menghafal F-key-nya sendiri tanpa pernah membaca panduan.

**Aturan yang menentukan bentuk layar ini:**

1. **Fokus selalu kembali ke kolom cari.** Setelah barang masuk keranjang, setelah dialog ditutup, setelah transaksi selesai. Kasir tidak pernah perlu mengklik untuk melanjutkan, dan scanner barcode, yang bekerja persis seperti keyboard, langsung berfungsi tanpa penyesuaian apa pun.
2. **Total adalah benda terbesar di layar.** Angka inilah yang diucapkan kasir ke pembeli puluhan kali sehari, dan sering dibaca sambil menoleh.
3. **Tidak ada animasi di jalur transaksi.** Transisi 200 milidetik dikali 300 transaksi sehari adalah satu menit yang hilang, ditambah rasa lambat yang tidak perlu.
4. **Baris terakhir selalu tersorot**, sehingga F2/F3 bekerja pada baris yang benar tanpa dipilih dulu.
5. **Bilah status tidak pernah kosong** ([bab 05](05-sinkronisasi-offline.md) §5.6).
6. **Setiap tindakan punya dua jalan: pintasan papan ketik dan tombol layar.** Tidak ada satu pun tindakan yang hanya bisa dicapai lewat papan ketik, kalau ada, layar ini mati total di tablet.

### Tombol pintas dan syarat Fn-lock

Pintasannya **hanya F-key**, tanpa alternatif `Ctrl`:

| Tindakan | Tombol |
|---|---|
| Ubah jumlah baris terakhir | `F2` |
| Hapus baris terakhir | `F3` |
| Diskon nota | `F4` |
| Gantung transaksi | `F6` |
| Bayar | `F9` |
| Batal | `Esc` |

Satu set tombol saja lebih mudah dihafal, dan inilah yang lazim di mesin kasir toko lain, kasir berpengalaman langsung mengenalinya.

> **Syarat pemasangan di laptop.** Di kebanyakan laptop, baris tombol F dipakai untuk volume dan kecerahan, sehingga `F9` sebenarnya menuntut `Fn+F9`, dua tangan, ratusan kali sehari. **Laptop kasir wajib disetel Fn-lock** (lewat BIOS, atau `Fn+Esc` pada banyak merek) sebagai bagian dari pemasangan awal, dan setelan itu perlu diperiksa ulang setiap kali laptopnya diganti atau BIOS-nya direset.
>
> Ini utang yang disengaja: kenyamanan sehari-hari ditukar dengan satu langkah pemasangan yang bisa terlupa. Kalau kelak ternyata sering terlupa, tambahkan alternatif `Ctrl+huruf`, bukan mengganti F-key.

Perangkat sentuh tidak terpengaruh sama sekali, karena setiap tindakan juga punya tombolnya sendiri (aturan #6).

### Dialog pembayaran

```
┌──────────────────────────────────────┐
│  Total            Rp 39.500          │
│                                      │
│  Tunai  [ 50.000            ]        │
│                                      │
│  [ Uang pas ] [ 50rb ] [ 100rb ]     │
│                                      │
│  Kembalian        Rp 10.500          │
│                                      │
│  Metode: (•) Tunai ( ) Transfer      │
│                                      │
│         [ Esc Batal ]  [ Enter ▸ ]   │
└──────────────────────────────────────┘
```

Kembalian dihitung saat diketik, bukan setelah dikonfirmasi, kasir sering mengambil uang kembalian sebelum menekan tombol terakhir.

### Setelah bayar, tanpa langkah cetak

Toko belum punya printer, jadi **cetak bukan bagian dari alur menyelesaikan transaksi.** Setelah pembayaran dikonfirmasi, layar langsung menampilkan ringkasan dengan kembalian sebagai angka terbesar:

```
┌──────────────────────────────────────┐
│  ✓  Nota 20260807-K1-0007 tersimpan  │
│                                      │
│         KEMBALIAN                    │
│        Rp 10.500                     │
│                                      │
│  [ Cetak struk ]   [ Enter ▸ Baru ]  │
└──────────────────────────────────────┘
```

`Enter` langsung membuka transaksi berikutnya. Tombol **Cetak struk** ada di sana untuk dipakai kalau printer tersedia, tetapi tidak pernah menghalangi.

Ada pengaturan `cetak_otomatis` yang **mati secara bawaan**. Saat printer dibeli (M8), pemilik menyalakannya dan dialog cetak muncul sendiri setelah setiap transaksi, tanpa perlu ubah kode.

Nota lama selalu bisa dicetak ulang dari daftar penjualan, sehingga struk yang gagal tercetak bukan kejadian yang perlu ditakuti.

## 6.4 Dashboard pemilik (HP)

```
┌───────────────────────┐
│  Toko Berkah       ☰  │
├───────────────────────┤
│  HARI INI             │
│  ┌─────────┬────────┐ │
│  │ Omzet   │ Laba   │ │
│  │ 2,4 jt  │ 410 rb │ │
│  └─────────┴────────┘ │
│  37 transaksi         │
├───────────────────────┤
│  PERLU PERHATIAN      │
│  ⚠ 6 barang menipis  ›│
│  ⚠ 2 hutang jatuh    ›│
│     tempo minggu ini  │
│  ⚠ 3 produk belum    ›│
│     dilengkapi        │
├───────────────────────┤
│  TERLARIS HARI INI    │
│  1. Indomie Goreng 42 │
│  2. Teh Botol      28 │
│  3. Beras Pandan   19 │
└───────────────────────┘
```

Bagian "Perlu perhatian" sengaja diletakkan di atas daftar terlaris. Angka penjualan menyenangkan untuk dilihat, tetapi yang menuntut tindakan hari itu adalah stok menipis dan hutang jatuh tempo.

## 6.5 Opname di HP

```
┌───────────────────────┐
│ ←  Opname #4          │
│ Sembako · 12/40 baris │
├───────────────────────┤
│ Beras Pandan Wangi    │
│ sistem  42,5 kg       │
│ fisik  [ 41,0 ]  −1,5 │
├───────────────────────┤
│ Gula Pasir            │
│ sistem  18,0 kg       │
│ fisik  [      ]       │
├───────────────────────┤
│ Minyak Goreng 1L      │
│ sistem  24 botol      │
│ fisik  [ 24 ]     0   │
├───────────────────────┤
│  [ Simpan draft ]     │
└───────────────────────┘
```

Satu produk satu blok, kolom isian besar dan langsung bisa diketik. Draf tersimpan otomatis setiap kali satu baris terisi, karena opname sering terpotong, ada pembeli datang, ada telepon masuk.

## 6.6 Prinsip yang berlaku di semua layar

**Angka.** Uang selalu rata kanan dengan pemisah ribuan gaya Indonesia (`Rp 39.500`). Jumlah berdesimal memakai koma (`1,5 kg`), dan desimal nol tidak ditampilkan (`24 botol`, bukan `24,000 botol`).

**Kontras.** Toko sering terang oleh cahaya matahari, dan layar kasir sering murah. Teks abu muda di atas putih tidak terbaca di sana. Warna teks utama minimal berkontras 7:1 terhadap latarnya.

**Konfirmasi seperlunya.** Hanya untuk tindakan yang tidak bisa dibatalkan: memposting opname, menerima faktur pembelian, menutup sesi kas, membatalkan keranjang berisi. Dialog konfirmasi untuk hal sepele melatih orang menekan "Ya" tanpa membaca, dan itu justru merusak penjagaan yang sungguhan.

**Pesan kesalahan** berbahasa Indonesia, menyebut apa yang salah dan apa yang harus dilakukan, ditampilkan di samping kolom penyebabnya. Bukan "Terjadi kesalahan", melainkan "Faktor satuan harus lebih besar dari 0".

**Batas lebar layar:** 360 px (HP kecil) → 768 px (tablet) → 1024 px ke atas (kasir).

Setiap layar **dapat dioperasikan penuh sejak 360 px**, termasuk layar kasir. Di bawah 1024 px, susunan dua kolomnya bertumpuk: keranjang di atas, ringkasan dan tombol bayar menempel di bawah layar agar selalu terjangkau ibu jari. Yang berubah cuma tata letaknya; tidak ada tindakan yang hilang.

Batas ini diperiksa oleh uji ujung-ke-ujung pada tiga ukuran, bukan sekadar dilihat sekilas ([bab 10 §10.3](10-strategi-pengujian.md#103-tiga-lapis)).

**Tanpa mode gelap di v1.** Toko beroperasi siang hari di ruang terang. Menambahkannya berarti menggandakan pekerjaan pemeriksaan kontras tanpa ada yang meminta.
