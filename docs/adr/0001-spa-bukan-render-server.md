# ADR-0001 — Aplikasi satu halaman, bukan render di server

- **Tanggal:** 2026-08-07
- **Status:** Diterima

## Konteks

Internet toko sering terganggu. Kasir tidak boleh berhenti melayani pembeli karena itu.

## Keputusan

Antarmuka dibangun sebagai **aplikasi satu halaman (SPA)** dengan React + Vite, dipasang sebagai PWA. Tidak ada render di sisi server.

## Alasan

Halaman yang dirender server membutuhkan server saat dibuka — persis sumber daya yang hilang ketika internet mati, dan justru saat itulah kasir paling butuh aplikasinya terbuka.

Tidak ada satu pun kebutuhan di [bab 01](../perancangan/01-kebutuhan.md) yang memerlukan render server: tidak ada halaman publik, tidak ada kebutuhan SEO, tidak ada tautan yang dibagikan ke luar. Seluruh sistem berada di balik layar masuk.

## Alternatif yang ditolak

**Next.js dengan App Router.** Lebih dikenal untuk portofolio, dan itu pertimbangan yang nyata. Ditolak karena penelusuran halaman antar rute bergantung pada server kecuali semuanya dipaksa berjalan di sisi klien — yang berarti membayar seluruh kerumitan Next.js untuk kemudian mematikan bagian yang membuatnya berharga.

**Django dengan template.** Setiap halaman menuntut permintaan ke server. Tidak mungkin offline.

**Aplikasi desktop (Tauri/Electron).** Offline menjadi alami dan akses perangkat keras paling mulus. Ditolak karena pemilik perlu membuka sistem dari HP — itu berarti membangun dan merawat dua antarmuka, untuk toko yang cuma punya satu kasir.

## Konsekuensi

- Muatan awal lebih besar; diredam service worker sehingga hanya terasa sekali.
- Tidak ada SEO. Tidak dibutuhkan.
- Seluruh keadaan layar dikelola di browser, sehingga logika klien lebih berat — dan itu memang tempat yang benar untuknya di sini.
- Bila kelak dibutuhkan halaman publik ber-SEO (katalog daring, misalnya), itu proyek terpisah dengan penempatan terpisah.
