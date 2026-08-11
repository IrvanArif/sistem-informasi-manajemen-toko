# ADR-0009: PostgreSQL tersemat untuk pengembangan, tanpa Docker

- **Tanggal:** 2026-08-08
- **Status:** Diterima
- **Mengubah sebagian:** [ADR-0007](0007-lapisan-gratis-dan-portabilitas.md), khusus bagian "semua layanan dijalankan lewat `docker-compose.yml`". Sisa ADR-0007 tetap berlaku.

## Konteks

Rencana semula menjalankan PostgreSQL lokal lewat Docker Compose, dan menguji dengan `testcontainers` yang juga menuntut Docker.

Pemilik proyek menetapkan syarat tambahan: **tidak ada lagi perangkat lunak yang dipasang ke sistem laptopnya.** Docker menuntut hak `sudo`, memasang layanan latar, dan mengubah keanggotaan grup pengguna. Syarat itu menutup jalur Docker sepenuhnya untuk pengembangan lokal.

Pertanyaannya jadi: bagaimana tetap memakai PostgreSQL sungguhan tanpa memasang apa pun ke sistem?

## Keputusan

Pengembangan dan pengujian lokal memakai **`pgserver`** (Apache-2.0), paket Python yang membawa binari PostgreSQL 16 di dalamnya. Ia dipasang oleh `uv` ke dalam lingkungan virtual proyek, bukan ke sistem, dan menjalankan server pada soket Unix di folder proyek.

- Pengembangan lokal: `pgserver`, bukan Docker Compose.
- Uji integrasi: `pgserver`, bukan `testcontainers`.
- Penempatan kelak: tetap memakai `Dockerfile`, tetapi **dibangun di sisi penyedia**, sehingga Docker tidak perlu ada di laptop siapa pun.

## Alasan

Yang membuat [ADR-0002](0002-fastapi-bukan-django.md) dan [bab 10](../perancangan/10-strategi-pengujian.md) memilih PostgreSQL sungguhan alih-alih SQLite adalah tiga sifat yang tidak dimiliki SQLite. Ketiganya diverifikasi bekerja pada `pgserver` sebelum keputusan ini diambil:

| Sifat | Hasil verifikasi | Dibutuhkan oleh |
|---|---|---|
| `NUMERIC(14,3)` presisi penuh | `Decimal('1.500')` persis | Jumlah barang curah |
| `NUMERIC(14,4)` presisi penuh | `Decimal('2866.6667')` persis | HPP, [bab 03 §3.4](../perancangan/03-model-data.md) |
| `SELECT … FOR UPDATE` | didukung | Penguncian baris, [bab 03 §3.3](../perancangan/03-model-data.md) aturan #2 |
| `ENUM` asli | didukung | `peran`, `tipe` mutasi, `status` |

Karena mesin basis datanya **benar-benar PostgreSQL 16**, bukan tiruan atau lapisan kompatibilitas, tidak ada satu pun keputusan rancangan yang perlu dilonggarkan. Yang berubah hanya **cara menyalakannya**, bukan apa yang dinyalakan.

## Alternatif yang ditolak

**Memasang Docker.** Jalur semula. Ditolak karena bertentangan dengan syarat pemilik proyek, dan syarat itu masuk akal: laptop pribadi tidak perlu menanggung layanan latar demi satu proyek.

**Memasang PostgreSQL lewat `apt`.** Tetap berupa pemasangan ke sistem berikut layanan latar. Ditolak dengan alasan yang sama.

**Beralih ke SQLite.** Tanpa pemasangan apa pun karena sudah menyatu dengan Python. Ditolak karena SQLite tidak punya `NUMERIC` presisi sejati maupun penguncian per baris. Untuk sistem yang menghitung uang dan stok, dua kekurangan itu menyentuh persis bagian yang paling mahal bila salah, dan akan memaksa penulisan ulang saat M1 tiba.

**Menunda basis data sampai Docker tersedia.** Berarti M0 berhenti total. Ditolak.

## Konsekuensi

- Tidak ada `docker-compose.yml` untuk pengembangan. Basis data dinyalakan lewat perintah Python singkat.
- `testcontainers` dicoret dari dependensi.
- Data pengembangan tinggal di folder proyek dan diabaikan git, sehingga `docker compose down -v` diganti dengan sekadar menghapus foldernya.
- Alur CI memakai `pgserver` yang sama, sehingga lingkungan uji di komputer dan di CI benar-benar identik. Ini justru lebih baik daripada rencana semula, yang memakai `testcontainers` lokal dan layanan terpisah di CI.
- **Jaminan portabilitas ADR-0007 tetap utuh:** tidak ada fungsi khusus penyedia yang dipakai, dan `Dockerfile` untuk penempatan tetap ditulis. Yang hilang cuma keharusan Docker berjalan di laptop.
- Bila kelak ada anggota tim yang memakai Windows atau macOS, `pgserver` menyediakan binari untuk keduanya. Bila tidak, jalur Docker masih bisa ditambahkan kembali tanpa mengubah kode aplikasi.
