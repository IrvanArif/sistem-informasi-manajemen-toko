# 10. Strategi Pengujian

## 10.1 Apa yang benar-benar perlu diuji

Sistem ini memegang uang dan stok orang lain. Prioritasnya bukan cakupan baris kode, melainkan **keyakinan pada hal-hal yang salahnya paling mahal**:

| Prioritas | Bidang | Kalau salah, akibatnya |
|---|---|---|
| 1 | Perhitungan HPP dan laba | Pemilik salah menilai untung selama berbulan-bulan |
| 2 | Konversi satuan | Stok berbohong sejak minggu pertama |
| 3 | Buku besar stok | Selisih yang tak bisa dijelaskan |
| 4 | Idempotensi sinkronisasi | Omzet tercatat dua kali |
| 5 | Pembulatan uang | Kas tak pernah cocok |
| 6 | Hak akses | Kasir melihat harga modal |

Tampilan diuji paling sedikit. Tombol yang salah warna ketahuan dalam sekejap; HPP yang meleset Rp13 per dus tidak ketahuan berbulan-bulan.

## 10.2 Uji ditulis menyusul, tetapi wajib ada sebelum digabung

Kode ditulis lebih dulu, ujinya menyusul **di dalam tugas yang sama** — bukan ditunda ke "nanti kalau sempat". Gerbangnya bukan urutan penulisan, melainkan penggabungan: [alur CI](#105-otomasi) menolak cabang yang menyentuh `backend/app/layanan/` tanpa membawa uji.

Keputusan ini diambil sadar. Menulis uji lebih dulu memang menghasilkan rancangan yang lebih bersih, tetapi menuntut penguasaan `pytest` sejak hari pertama — sementara proyek ini sekaligus menjadi tempat belajar Python. Disiplin yang ditulis di dokumen lalu ditinggalkan di minggu kedua lebih buruk daripada disiplin yang lebih rendah tapi benar-benar dijalankan.

**Risiko yang diterima:** uji yang ditulis setelah kodenya cenderung memeriksa apa yang kebetulan sudah dikerjakan kode, bukan apa yang seharusnya dikerjakan. Kalau rumus HPP salah, uji yang ditulis dari kode itu akan meloloskannya dengan yakin.

**Peredamnya sudah tersedia, dan justru inilah gunanya menulis rancangan sebelum kode.** Contoh terhitung di [bab 03 §3.5](03-model-data.md#35-contoh-terhitung) — HPP `2.866,6667`, laba `Rp17.233`, beras `1,5 kg` senilai `Rp21.000` — ditulis **sebelum satu baris kode pun ada**. Angka-angka itu berasal dari rancangan, bukan dari keluaran program. Untuk bagian yang paling mahal kalau salah, jawabannya sudah dipatok lebih dulu, jadi urutan penulisan uji tidak lagi menentukan.

Karena itu aturannya: **untuk perhitungan uang dan stok, uji wajib memakai angka dari [bab 03 §3.5](03-model-data.md#35-contoh-terhitung), bukan angka yang disalin dari hasil menjalankan kode.** Kalau kode dan dokumen berbeda, yang salah adalah kodenya sampai terbukti sebaliknya.

Setiap uji dirujuk ke kode kebutuhannya (`KAS-04`, `BEL-04`, `AKS-05`, …) sehingga bisa ditelusuri dua arah.

## 10.3 Tiga lapis

```
        ╱ E2E ╲          sedikit — alur utuh, termasuk simulasi offline
      ╱─────────╲
    ╱ Integrasi  ╲       sedang — API + basis data sungguhan
  ╱───────────────╲
╱  Unit (layanan)  ╲     banyak — aturan bisnis murni, tanpa I/O
────────────────────
```

### Unit — `pytest`

Menguji isi `backend/app/layanan/` tanpa menyalakan server. Fungsi di sana menerima objek biasa dan sesi basis data, sehingga cepat dan tidak rapuh.

Kasus wajib:

| Berkas | Yang diuji |
|---|---|
| `test_hpp.py` | Rata-rata bergerak; stok awal nol; stok negatif memakai harga beli langsung; penjualan **tidak** mengubah HPP |
| `test_satuan.py` | `jumlah × faktor`; jumlah pecahan; faktor ≤ 0 ditolak; satuan dasar tunggal |
| `test_stok.py` | `saldo_sesudah` berurutan; mutasi tak bisa diubah; jumlah mutasi = salinan stok |
| `test_penjualan.py` | Subtotal per baris; diskon baris & nota; pembulatan nota Rp100/Rp500; laba memakai HPP tersimpan |
| `test_retur.py` | Retur melebihi asal ditolak; perubahan status nota; stok kembali |
| `test_pembelian.py` | Draft tidak menyentuh stok; penerimaan mengubah stok & HPP; faktur terkunci setelah diterima |
| `test_opname.py` | `stok_sistem` dibekukan saat pembuatan; posting menghasilkan mutasi |
| `test_sesi_kas.py` | Kas sistem; selisih tanpa catatan ditolak |

**Contoh terhitung di [bab 03 §3.5](03-model-data.md#35-contoh-terhitung) diterjemahkan langsung menjadi uji.** Angka-angka itu memang ditulis untuk keperluan ini.

### Uji properti — `Hypothesis`

Untuk konversi satuan dan pembulatan, contoh yang dipilih manusia cenderung terlalu rapi. Hypothesis membangkitkan ribuan kombinasi acak untuk memeriksa sifat yang harus selalu benar:

- Mengubah ke satuan dasar lalu kembali menghasilkan nilai semula
- Jumlah seluruh `subtotal` baris = `subtotal` nota, untuk kombinasi harga dan jumlah apa pun
- Setelah rangkaian mutasi apa pun, salinan stok = jumlah seluruh mutasi
- HPP tidak pernah negatif selama harga beli tidak negatif

### Integrasi — `pytest` + PostgreSQL sungguhan

Memakai PostgreSQL 16 asli lewat `pgserver`, bukan SQLite. Perbedaan perilaku `NUMERIC`, `SELECT … FOR UPDATE`, dan `ENUM` antara keduanya persis berada di bagian yang paling ingin kita percayai.

`pgserver` menjalankan PostgreSQL dari dalam lingkungan Python proyek, tanpa Docker dan tanpa pemasangan ke sistem ([ADR-0009](../adr/0009-postgresql-tersemat-tanpa-docker.md)). Karena alur CI memakai cara yang persis sama, lingkungan uji di komputer dan di CI benar-benar identik — bukan sekadar mirip.

Kasus wajib:

- `POST /penjualan` dua kali dengan `uuid_klien` sama → satu baris, jawaban `201` lalu `200`, stok terpotong sekali
- Tiga nota berbeda yang masing-masing memuat `produk_baru` ber-UUID sama → **satu** produk tercipta, terpakai di ketiganya
- Baris nota memuat `produk_id` sekaligus `produk_baru` → `422 RUJUKAN_PRODUK_GANDA`
- Dua penjualan bersamaan atas produk yang sama → `saldo_sesudah` berurutan, tidak ada yang tertimpa
- Kasir mengakses endpoint laporan → `403`
- Kasir mengakses `/pengguna` atau memposting opname → `403`
- Jawaban `/produk` **dan** `/sinkron/katalog` untuk kasir **tidak memuat** kolom `hpp`
- Menonaktifkan pemilik terakhir → `422 PEMILIK_TERAKHIR`; menonaktifkan akun bersesi kas terbuka → `422 SESI_KAS_MASIH_TERBUKA`
- Pengguna mengubah perannya sendiri → `422 PERAN_SENDIRI`
- Penerimaan faktur gagal di tengah → seluruhnya dibatalkan, stok tidak berubah
- `GET /sinkron/katalog?sejak=` hanya mengembalikan yang berubah

### E2E — `Playwright`

Sedikit tapi menyeluruh, mengikuti alur di [bab 04](04-alur-kerja.md):

1. **Satu hari kasir:** buka sesi → 3 transaksi (termasuk barang curah dan penjualan per dus) → tutup sesi dengan selisih → wajib isi catatan.
2. **Transaksi tanpa mouse (KAS-13):** seluruh alur diselesaikan hanya dengan papan ketik, memakai pintasan F-key.
3. **Transaksi tanpa papan ketik (KAS-15, NF-07):** alur yang sama diselesaikan hanya dengan sentuhan, pada `viewport` 360×640, 768×1024, dan 1280×800 — memastikan tidak ada tindakan yang cuma bisa dicapai lewat pintasan, tidak ada tombol yang terpotong, dan halaman tidak pernah bergeser ke samping.
4. **Offline penuh:** `context.set_offline(True)` → jual 3 barang → pastikan indikator 🔴 dan transaksi tetap selesai tanpa menuntut cetak → kembalikan koneksi → pastikan ketiganya sampai, tanpa duplikat, dan stok server berkurang tepat.
5. **Kirim ulang setelah jaringan putus di tengah:** paksa kegagalan setelah server menyimpan → pastikan pengiriman ulang tidak menggandakan.
6. **Tambah cepat saat offline (STK-05):** tambahkan satu barang kilat saat offline → jual di dua nota berbeda → sinkron → pastikan hanya **satu** produk tercipta dan terpakai di keduanya.
7. **Impor CSV** dengan beberapa baris rusak → pastikan pesan menyebut nomor baris yang benar.
8. **Opname di layar HP** (`viewport` 390×844) → isi sebagian → tinggalkan → kembali → draf masih ada.

Skenario 4, 5, dan 6 adalah yang paling penting di seluruh berkas uji, karena ketiganya menguji satu-satunya bagian sistem yang benar-benar sulit: memastikan pekerjaan kasir sampai ke server tepat satu kali.

## 10.4 Data uji

Ada satu berkas benih (`seed`) berisi toko contoh: 30 produk lintas kategori, sebagian bersatuan ganda, sebagian curah, beberapa pemasok, dan riwayat sebulan. Dipakai untuk pengembangan lokal, uji E2E, dan peragaan portofolio.

Uji tidak pernah bergantung pada urutan berkas uji lain, dan tidak pernah menyentuh basis data sungguhan.

## 10.5 Otomasi

`.github/workflows/uji.yml` berjalan pada setiap dorongan dan setiap permintaan tarik:

```
ruff  →  mypy  →  pytest (unit)  →  pytest (integrasi)  →  vitest  →  playwright
                              ↘  pip-audit  +  npm audit  ↙
```

Gagal di tahap mana pun menghentikan seluruh alur. Cabang utama tidak menerima gabungan bila alur ini merah.

**Gerbang tambahan yang menggantikan disiplin uji-dulu** ([§10.2](#102-uji-ditulis-menyusul-tetapi-wajib-ada-sebelum-digabung)): bila sebuah cabang mengubah berkas di `backend/app/layanan/` tanpa menyertakan perubahan di `backend/tests/`, alur CI menolaknya dengan pesan yang menyebut berkas mana yang belum berteman uji. Karena uji tidak lagi datang lebih dulu secara alami, gerbang inilah yang memastikan ia tidak pernah tertinggal.

## 10.6 Yang tidak diuji

Ditulis terang-terangan supaya kelalaiannya disengaja, bukan kebetulan:

- **Tampilan visual.** Tidak ada uji cuplikan gambar. Rapuh, dan salahnya murah.
- **Layanan pihak ketiga.** Cloudflare, Render, dan Neon dianggap bekerja.
- **Ketahanan beban.** Satu kasir tidak menghasilkan beban yang perlu diukur.
- **Kompatibilitas peramban lama.** Sasarannya Chrome dan Edge versi terbaru pada mesin kasir.
