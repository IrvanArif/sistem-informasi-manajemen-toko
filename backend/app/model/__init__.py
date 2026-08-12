"""Seluruh tabel didaftarkan di sini, di satu tempat.

Model yang tidak pernah diimpor tidak terdaftar di metadata SQLAlchemy.
Akibatnya dua hal yang sama-sama sulit dilacak: pembuatan tabel untuk uji
gagal dengan keluhan kunci asing yang tampak tak masuk akal, dan
--autogenerate menganggap tabelnya tidak ada lalu menulis migrasi yang
menghapusnya.

Mengumpulkan impornya di sini membuat satu impor `app.model` cukup untuk
mendapatkan semuanya. Tabel baru cukup ditambahkan ke daftar ini.
"""

from app.model.dasar import Dasar, KolomWaktu
from app.model.kategori import Kategori
from app.model.mutasi import MutasiStok, TipeMutasi
from app.model.pengguna import Pengguna, Peran
from app.model.percobaan_masuk import PercobaanMasuk
from app.model.produk import JUMLAH, TARIF, Produk, SatuanProduk
from app.model.token import TokenSegar

__all__ = [
    "JUMLAH",
    "TARIF",
    "Dasar",
    "Kategori",
    "KolomWaktu",
    "MutasiStok",
    "Pengguna",
    "PercobaanMasuk",
    "Peran",
    "Produk",
    "SatuanProduk",
    "TipeMutasi",
    "TokenSegar",
]
