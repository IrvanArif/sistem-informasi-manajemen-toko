# Catatan Keputusan Arsitektur (ADR)

Setiap berkas di sini mencatat **satu keputusan**: apa konteksnya, apa yang diputuskan, kenapa, apa alternatif yang ditolak, dan apa konsekuensinya.

Gunanya bukan dokumentasi. Gunanya adalah supaya enam bulan lagi — saat ada yang bertanya "kenapa tidak pakai FIFO saja?" — jawabannya sudah tertulis lengkap dengan alasan yang berlaku saat itu, dan bisa dinilai apakah alasannya masih berlaku.

**ADR tidak diubah setelah diterima.** Kalau keputusannya berubah, tulis ADR baru yang menggantikannya dan tandai yang lama sebagai `Digantikan oleh ADR-XXXX`. Riwayat keputusan sama berharganya dengan keputusannya sendiri.

| # | Keputusan | Status |
|---|---|---|
| [0001](0001-spa-bukan-render-server.md) | Aplikasi satu halaman, bukan render di server | Diterima |
| [0002](0002-fastapi-bukan-django.md) | FastAPI, bukan Django | Diterima |
| [0003](0003-hpp-rata-rata-bergerak.md) | HPP rata-rata bergerak, bukan FIFO | Diterima |
| [0004](0004-offline-hanya-untuk-menjual.md) | Offline hanya untuk menjual | Diterima |
| [0005](0005-satuan-bertingkat.md) | Satuan bertingkat dengan jumlah berdesimal | Diterima |
| [0006](0006-stok-boleh-minus.md) | Stok boleh minus | Diterima |
| [0007](0007-lapisan-gratis-dan-portabilitas.md) | Lapisan gratis, dijaga tetap bisa dipindah | Diterima, sebagian diubah [0009](0009-postgresql-tersemat-tanpa-docker.md) |
| [0008](0008-istilah-domain-bahasa-indonesia.md) | Istilah domain memakai bahasa Indonesia | Diterima |
| [0009](0009-postgresql-tersemat-tanpa-docker.md) | PostgreSQL tersemat untuk pengembangan, tanpa Docker | Diterima |
