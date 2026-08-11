# ADR-0002: FastAPI, bukan Django

- **Tanggal:** 2026-08-07
- **Status:** Diterima

## Konteks

Sisi server memakai Python, sebagian karena cocok untuk pekerjaannya, sebagian karena pemilik proyek ingin mempelajari Python. Antarmuka sepenuhnya dipegang React ([ADR-0001](0001-spa-bukan-render-server.md)), sehingga server hanya menyediakan API JSON.

## Keputusan

**FastAPI** + SQLAlchemy 2.0 + Alembic + Pydantic v2, dikelola dengan `uv`.

## Alasan

FastAPI membangkitkan spesifikasi OpenAPI langsung dari model Pydantic, dan dari situ tipe TypeScript untuk sisi browser dibangkitkan otomatis. Kontrak antara Python dan browser jadi punya **satu sumber kebenaran, ditulis di Python**: mengubah bentuk data produk di server membuat sisi browser gagal dikompilasi bila tidak ikut menyesuaikan.

Untuk proyek dua bahasa yang dikerjakan sambil belajar, jaring pengaman itu bernilai tinggi.

Permukaan yang perlu dipelajari juga lebih kecil, Pydantic, SQLAlchemy, dan rute, tanpa konvensi kerangka yang harus dihafal lebih dulu.

## Alternatif yang ditolak

**Django + Django REST Framework.** Lebih lengkap sejak awal: otentikasi, migrasi, dan panel admin bawaan. Panel admin itu menggoda karena memberi pengelolaan data master tanpa menulis UI.

Ditolak karena panel admin Django tetap tidak layak diserahkan ke pemilik toko, sehingga UI-nya harus dibuat juga, keuntungannya tinggal separuh. Dan karena tampilan sepenuhnya dipegang React, sebagian besar kekuatan Django (template, form, admin) tidak terpakai. Yang tersisa cuma ORM dan migrasi, yang keduanya juga tersedia di jalur ini.

**Flask.** Terlalu sedikit bawaan; validasi dan OpenAPI harus dirakit sendiri.

## Konsekuensi

- Otentikasi, hak akses, dan pembatasan percobaan masuk ditulis sendiri, tidak diwarisi kerangka. Lebih banyak kode, tetapi juga lebih sedikit hal yang bekerja tanpa dipahami.
- Tidak ada panel admin gratis; seluruh pengelolaan data master butuh UI. Sudah masuk lingkup M1.
- Migrasi ditangani Alembic yang berdiri sendiri, bukan bagian kerangka.
