# 09. Penanganan Error

## 9.1 Kegagalan yang diperkirakan bukanlah error

Stok habis, internet putus, barcode ganda, selisih kas, semua itu **kejadian normal di toko**, bukan kelainan. Ia layak mendapat cabang alur yang dirancang, bukan pesan "Terjadi kesalahan" yang menyerah.

Yang benar-benar error adalah hal yang seharusnya mustahil: buku besar tidak cocok dengan salinan stok, total nota berbeda dari penjumlahan barisnya, HPP menjadi negatif. Untuk itu sistem **berhenti keras dan berisik**, karena melanjutkan berarti menulis data yang salah.

Pembedaan ini menentukan tanggapan:

| | Kegagalan yang diperkirakan | Error sesungguhnya |
|---|---|---|
| Contoh | Jaringan putus, stok minus, sandi salah | Buku besar tidak cocok, total tidak konsisten |
| Tanggapan | Cabang alur, pesan yang menuntun | Gagalkan transaksi, catat lengkap, beri tahu |
| Pengguna melihat | Penjelasan dan langkah berikutnya | "Terjadi kesalahan sistem" + kode rujukan |
| Boleh dilanjutkan? | Ya | Tidak |

## 9.2 Empat lapis penjagaan

```
① Perangkat   bentuk masukan       "Jumlah harus diisi"
② Server      aturan bisnis        "Retur melebihi jumlah pada nota asal"
③ Basis data  batasan & kunci      UNIQUE, CHECK, FOREIGN KEY, SELECT FOR UPDATE
④ Pemeriksa   ketidakcocokan       kueri pemeriksa buku besar (bab 03 §3.3)
```

Setiap lapis mengasumsikan lapis sebelumnya bisa dilewati. Lapis ① semata kenyamanan. Ia membuat kesalahan ketik ketahuan tanpa menunggu jaringan, dan tidak pernah menjadi satu-satunya penjaga. Lapis ③ adalah jaring terakhir yang tidak bisa dibujuk oleh bug di lapis mana pun.

## 9.3 Transaksi basis data

Setiap operasi yang menyentuh stok atau uang berjalan dalam **satu transaksi**: penjualan, penerimaan barang, posting opname, retur, penyesuaian.

Pola bakunya:

```python
with sesi.begin():
    produk = kunci_baris_produk(sesi, produk_id)   # SELECT … FOR UPDATE
    saldo_baru = produk.stok + jumlah
    hpp_baru = hitung_hpp(produk, jumlah, harga)
    tulis_mutasi(sesi, produk, jumlah, saldo_baru, hpp_baru)
    produk.stok = saldo_baru
    produk.hpp = hpp_baru
```

Kalau langkah mana pun gagal, seluruhnya dibatalkan. Tidak pernah ada keadaan setengah jadi berupa mutasi tertulis sementara stok tidak ikut berubah.

Penguncian baris bukan kehati-hatian berlebihan: dua penjualan yang tiba nyaris bersamaan, hal biasa saat antrean offline dikirim beruntun, akan membaca saldo yang sama dan menulis `saldo_sesudah` yang keliru tanpa penguncian.

## 9.4 Peta kegagalan

| Kegagalan | Terdeteksi di | Tanggapan sistem | Yang dilihat pengguna |
|---|---|---|---|
| Jaringan putus saat menyimpan nota | Perangkat | Masuk antrean | merah Offline · penjualan lanjut |
| Server tidak menjawab | Perangkat | Coba lagi dengan jeda menaik | kuning *n* menunggu |
| Nota ditolak (422) | Server | Hentikan percobaan, tandai | + alasan + tombol tindakan |
| Token kedaluwarsa | Server | Minta masuk, lanjutkan antrean | Layar masuk, lalu kembali |
| Stok jadi minus | Server | Terima, catat, beri tahu dua tingkat | Kasir: catatan sekilas · Pemilik: daftar di dashboard |
| Barcode ganda saat impor | Server | Tolak baris itu saja | Nomor baris + barcode bentrok |
| Barcode ganda saat simpan produk | Basis data | `UNIQUE` menolak | "Barcode sudah dipakai *nama produk*" |
| Faktor satuan ≤ 0 | Server | Tolak | "Faktor satuan harus lebih besar dari 0" |
| Retur melebihi asal | Server | Tolak | "Nota ini hanya menyisakan 2 bungkus" |
| Selisih kas tanpa catatan | Server | Tolak penutupan | "Isi catatan untuk selisih Rp15.000" |
| Antrean belum kosong saat tutup sesi | Perangkat + server | Tolak penutupan | "Tunggu 3 transaksi terkirim" |
| Impor CSV berkolom salah | Server | Tolak seluruh berkas | Daftar kolom yang diharapkan |
| Buku besar ≠ salinan stok | Pemeriksa | Catat sebagai error berat, beri tahu | Peringatan di dashboard pemilik |
| HPP jadi negatif | Server | Gagalkan transaksi | "Terjadi kesalahan sistem" + kode |
| Basis data tidak terjangkau | Server | `503`, jangan pura-pura berhasil | kuning antrean tetap aman |

### Peringatan ditujukan pada orang yang bisa menindaklanjutinya

Stok minus adalah contoh terbaiknya, dan penanganannya dibagi dua tingkat:

| Siapa | Apa yang dilihat | Kenapa begitu |
|---|---|---|
| **Kasir** | Catatan kecil `Indomie · stok −3` yang hilang sendiri setelah beberapa detik. Tidak menghentikan apa pun, tidak perlu ditutup. | Ia perlu tahu ada yang janggal selagi barangnya masih di tangan, tetapi ia **tidak berhak** menyesuaikan stok ([bab 08 §8.1](08-keamanan-dan-peran.md#81-dua-peran)), jadi menuntut tindakan darinya cuma menahan antrean tanpa hasil. |
| **Pemilik** | Baris "N barang berstok minus ›" di dashboard, tertaut ke daftarnya. | Dia yang bisa membereskannya, lewat penyesuaian atau opname. |

> **Yang sengaja tidak dipakai: dialog yang harus diakui kasir.** Di toko yang katalognya belum lengkap, stok minus akan muncul puluhan kali sehari. Dialog sesering itu akan ditutup tanpa dibaca dalam hitungan hari, dan kebiasaan menutup dialog tanpa membaca terbawa ke dialog yang benar-benar penting, seperti konfirmasi posting opname. Penjagaan yang dilatih untuk diabaikan merusak penjagaan lain di sekitarnya.

Aturan umumnya: **peringatan hanya ditujukan pada orang yang punya wewenang menindaklanjutinya.** Memberi tahu orang yang tidak bisa berbuat apa-apa bukan transparansi. Itu kebisingan, dan kebisingan menumpulkan perhatian terhadap peringatan yang sungguhan.

## 9.5 Aturan menulis kode penanganan error

**Jangan pernah menelan kesalahan.**

```python
# SALAH, kegagalan lenyap tanpa jejak
try:
    perbarui_stok(produk, jumlah)
except Exception:
    pass

# BENAR, tangani yang dikenali, biarkan sisanya naik
try:
    perbarui_stok(produk, jumlah)
except StokTidakCukup as e:
    catat.peringatan("stok minus", produk_id=produk.id, kurang=e.kurang)
    raise
```

`except` tanpa jenis, dan `except` yang hanya `pass`, dilarang. Kegagalan yang tertelan akan muncul kembali berminggu-minggu kemudian sebagai selisih stok yang tidak bisa dijelaskan siapa pun, dan pada titik itu jejaknya sudah hilang.

**Nilai kembalian pengganti juga bentuk penelanan.** Fungsi yang mengembalikan `0` saat gagal menghitung HPP jauh lebih berbahaya daripada fungsi yang melempar kesalahan, karena `0` terlihat seperti jawaban yang sah dan akan mengalir diam-diam ke laporan laba.

**Pesan menyebutkan langkah berikutnya.** Bukan "Data tidak sah", melainkan "Faktor satuan harus lebih besar dari 0". Bukan "Gagal menyimpan", melainkan "Barcode 8991002101234 sudah dipakai Indomie Goreng".

## 9.6 Pencatatan

Catatan berbentuk JSON terstruktur (`structlog`, lisensi MIT/Apache), setiap permintaan membawa `id_permintaan` yang juga dikembalikan di kepala jawaban, sehingga keluhan pengguna bisa langsung ditelusuri ke barisnya.

| Tingkat | Dipakai untuk |
|---|---|
| `INFO` | Penjualan tersimpan, faktur diterima, opname diposting |
| `WARNING` | Stok minus, harga menyimpang >20%, jam perangkat meleset, masuk gagal |
| `ERROR` | Kegagalan tak terduga, ketidakcocokan buku besar, `5xx` |

**Yang tidak pernah dicatat:** sandi, token, dan isi cadangan.

Kesalahan yang sampai ke pengguna sebagai "kesalahan sistem" selalu disertai `id_permintaan` yang bisa dibacakan lewat telepon.
