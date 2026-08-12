# Menjalankan di localhost tanpa nomor port

Tujuannya membuka sistem di `http://localhost/toko`, seperti aplikasi lain
yang sudah ada di komputer ini.

## Kenapa tidak cukup memindahkan folder

Aplikasi PHP bisa diperlakukan begitu karena Apache menjalankan PHP di
dalam dirinya sendiri. Proyek ini berbeda:

- Sisi Python butuh **proses yang berjalan sendiri**. Apache tidak bisa
  menjalankannya seperti PHP.
- Sisi React harus **dibangun dulu** menjadi berkas statis. Berkas sumber
  `.tsx` tidak bisa dibaca browser.

Dan yang lebih menentukan: Apache bawaan Ubuntu hanya menolak berkas
berawalan `.ht`. Menaruh seluruh proyek di bawah folder yang dilayani
Apache berarti `backend/.env`, `kredensial-lokal.md`, `.git/`, dan isi
basis data bisa diunduh siapa pun yang menjangkau server itu.

## Susunan yang dipakai

```
~/Documents/Toko/            sumber, TIDAK dipindah ke mana pun
  backend/                     berjalan sebagai layanan di 127.0.0.1:8000
  frontend/                    sumber React

/var/www/html/toko/          HANYA hasil bangun React, berkas statis
```

Apache melayani berkas statis, dan meneruskan permintaan `/toko/api/`
kepada proses Python. Browser melihat semuanya di satu alamat, sehingga
tidak ada nomor port dan tidak ada urusan lintas-asal.

## Pemasangan sekali jalan

Bagian ini menuntut `sudo` karena mengubah pengaturan Apache:

```bash
cd ~/Documents/Toko
sudo cp deploy/apache-toko.conf /etc/apache2/conf-available/toko.conf
sudo a2enmod proxy proxy_http
sudo a2enconf toko
sudo systemctl reload apache2
```

Backend sudah dipasang sebagai layanan pengguna, tanpa `sudo`:

```bash
systemctl --user status toko-backend     # lihat keadaannya
systemctl --user restart toko-backend    # muat ulang setelah ubah kode
journalctl --user -u toko-backend -f     # ikuti catatannya
```

## Setelah mengubah tampilan

Berkas statis tidak ikut berubah sendiri. Bangun ulang:

```bash
cd ~/Documents/Toko/frontend
npm run build:www
```

## Dua cara menjalankan, keduanya berguna

| | `http://localhost/toko` | `http://localhost:5173` |
|---|---|---|
| Untuk | Pemakaian sehari-hari | Mengembangkan |
| Perubahan tampilan | Perlu `npm run build:www` | Langsung terlihat |
| Backend | Layanan systemd | Layanan systemd yang sama |

Keduanya bisa hidup bersamaan. Saat menyunting tampilan, `npm run dev`
jauh lebih enak karena perubahannya langsung tampak tanpa membangun ulang.

## Memeriksa hasilnya

```bash
curl -s http://localhost/toko/api/v1/sehat     # {"status":"sehat"}
curl -sI http://localhost/toko/ | head -1      # HTTP/1.1 200 OK
```

Bila yang pertama menjawab 404, modul proxy belum aktif atau Apache belum
dimuat ulang. Bila yang kedua menjawab 403, periksa izin baca folder
`/var/www/html/toko`.

## Uji offline di browser sungguhan

Kemampuan bekerja tanpa internet tidak bisa dibuktikan oleh uji satuan.
Service worker hanya ada di hasil bangun, dan hanya browser sungguhan yang
bisa dimatikan jaringannya lalu disegarkan. Karena itu uji ini dijalankan
terhadap `http://localhost/toko`, bukan terhadap server pengembangan.

Sekali saja, siapkan akun pengujinya:

```bash
cd ~/Documents/Toko/frontend
cp .env.e2e.contoh .env.e2e     # lalu isi dengan akun pengembangan
npx playwright install chromium
```

`.env.e2e` tidak pernah ikut terkirim ke repositori. Sandi yang telanjur
masuk riwayat git tidak bisa ditarik kembali, dan repositori ini publik.

Setiap kali tampilan berubah, bangun ulang lebih dulu. Uji ini membaca apa
yang dilayani Apache, bukan apa yang ada di kode:

```bash
npm run build:www
npm run test:e2e
```

Empat hal yang dijaganya:

| Uji | Yang runtuh bila gagal |
|---|---|
| Katalog tersalin ke perangkat | Pencarian barang mati saat internet putus. |
| Menjual saat internet mati, lalu antrean terkirim sendiri | Toko berhenti melayani, atau penjualan hilang. |
| Tiga transaksi offline terkirim tanpa duplikat | Stok dan uang tercatat ganda. |
| Aplikasi tetap terbuka setelah dimuat ulang tanpa internet | Kasir terkunci di luar, sebab masuk kembali menuntut server. |
