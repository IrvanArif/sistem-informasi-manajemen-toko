# ADR-0007: Lapisan gratis, dijaga tetap bisa dipindah

- **Tanggal:** 2026-08-07
- **Status:** Diterima. Bagian "semua layanan dijalankan lewat `docker-compose.yml`" diubah oleh [ADR-0009](0009-postgresql-tersemat-tanpa-docker.md); sisanya tetap berlaku.

## Konteks

Pemilik proyek menetapkan seluruh perkakas harus gratis atau open source, tanpa biaya berlangganan. Sementara itu, sistem harus bisa dibuka dari luar toko lewat internet, yang berarti ada komputer yang menyala terus di suatu tempat.

Seluruh **perangkat lunaknya** memang sudah gratis: Python, FastAPI, SQLAlchemy, PostgreSQL, React, Vite, Tailwind, semuanya berlisensi MIT, Apache, ISC, PSF, atau PostgreSQL License. Yang berbiaya hanyalah tempat menjalankannya.

## Keputusan

Memakai gabungan lapisan gratis:

| Lapisan | Layanan | Batasan yang diterima |
|---|---|---|
| Tampilan statis | Cloudflare Pages | Tidak ada |
| API Python | Render (gratis) | Tidur setelah 15 menit menganggur, bangun ~50 detik |
| PostgreSQL | Neon (gratis) | 0,5 GB penyimpanan |
| Cadangan | GitHub Actions | 90 hari masa simpan artefak |

Dan **menjaga agar seluruhnya bisa dipindah**: semua layanan dijalankan lewat `docker-compose.yml` yang sama seperti di komputer pengembangan. Tidak ada fungsi khusus penyedia yang dipakai, tanpa fungsi tanpa-server milik vendor, tanpa penyimpanan berkas berpemilik, tanpa otentikasi bawaan penyedia.

## Alasan

Soal tidur-bangun Render terdengar merusak, tetapi **antrean offline kebetulan menutupi persis masalah itu**: transaksi pertama pagi hari masuk antrean lokal dan terkirim sendiri saat server bangun. Kasir tidak pernah melihat penantian itu. Dua keputusan yang diambil karena alasan berbeda ternyata saling melengkapi.

Kapasitas 0,5 GB memberi ruang bertahun-tahun: dengan 100 transaksi sehari berisi rata-rata 5 barang, satu tahun menghasilkan sekitar 40 MB sebelum indeks.

## Alternatif yang ditolak

**Oracle Cloud Always Free.** Mesin virtual gratis permanen dengan 4 inti dan 24 GB RAM, tanpa tidur-bangun, dan mengajarkan penempatan sungguhan. Ditolak pada tahap ini karena pendaftarannya menuntut kartu untuk verifikasi dan ketersediaan mesin gratisnya tidak menentu. Tetap menjadi tujuan pindah yang paling masuk akal bila lapisan gratis sekarang berubah aturan.

**VPS berbayar (~Rp70.000/bulan).** Paling andal dan paling sederhana, tetapi bertentangan dengan batasan tanpa biaya.

**Komputer toko sebagai server + Tailscale.** Benar-benar tanpa biaya bulanan dan datanya berada di toko. Ditolak karena komputer toko harus selalu menyala, HP harus memasang aplikasi VPN, dan kerusakan satu komputer mematikan seluruh sistem tanpa cadangan otomatis.

## Konsekuensi

- **Aturan lapisan gratis bisa berubah sewaktu-waktu.** Ini risiko usaha yang nyata, bukan sekadar catatan teknis. Peredamnya adalah pencadangan harian ke tempat yang berbeda dari basis datanya, dan penempatan yang bisa dipindah.
- Otentikasi tidak bisa memakai cookie `httpOnly`, karena tampilan dan API berada di domain berbeda. Alasan dan peredamnya di [bab 08 §8.2](../perancangan/08-keamanan-dan-peran.md).
- Tidak boleh ada ketergantungan pada fungsi khusus penyedia. Setiap godaan ke arah itu harus ditolak, meski memangkas pekerjaan hari ini.
- Bila toko tumbuh, pindah ke VPS berbayar cukup mengganti berkas konfigurasi, bukan menulis ulang.
