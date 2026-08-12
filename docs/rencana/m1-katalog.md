# Rencana Implementasi M1: Katalog

**Tujuan:** Seluruh barang toko masuk sistem, lengkap dengan satuan bertingkat dan stok awalnya, sehingga M2 punya sesuatu untuk dijual.

**Arsitektur:** Melanjutkan pola M0 tanpa pola baru: `rute` tipis memanggil `layanan`, `layanan` memegang aturan dan tidak tahu HTTP, `model` memegang bentuk data. Yang baru hanyalah bahwa aturannya kini menyangkut uang dan stok, sehingga ketelitiannya lebih menentukan.

**Acuan:** [Bab 03 Model Data](../perancangan/03-model-data.md) · [Bab 04 Alur Kerja](../perancangan/04-alur-kerja.md) · [ADR-0005 Satuan bertingkat](../adr/0005-satuan-bertingkat.md) · [ADR-0006 Stok boleh minus](../adr/0006-stok-boleh-minus.md)

## Batasan Global

Seluruh batasan M0 tetap berlaku. Yang berikut ini mulai mengikat di M1:

| # | Batasan | Sumber |
|---|---|---|
| K1 | **Jumlah barang `NUMERIC(14,3)` dan `Decimal`, tidak pernah `float`.** Berlaku di basis data, Python, dan JSON (dikirim sebagai string). | [Bab 02 §2.5](../perancangan/02-arsitektur.md) |
| K2 | **HPP `NUMERIC(14,4)`**, satu-satunya pengecualian dari aturan uang bilangan bulat. | [Bab 03 §3.4](../perancangan/03-model-data.md) |
| K3 | **Buku besar stok adalah sumber kebenaran.** Kolom `produk.stok` hanya salinan cepat, dan keduanya ditulis dalam satu transaksi. | [Bab 03 §3.3](../perancangan/03-model-data.md) |
| K4 | **`mutasi_stok` hanya menerima penambahan.** Tidak ada `UPDATE`, tidak ada `DELETE`. Koreksi selalu baris baru. | [Bab 03 §3.2](../perancangan/03-model-data.md) |
| K5 | **Stok boleh minus**, dicatat dan diperingatkan, tidak pernah menghalangi. | [ADR-0006](../adr/0006-stok-boleh-minus.md) |
| K6 | **Harga tiap satuan ditulis sendiri**, bukan dihitung dari perkalian faktor. | [ADR-0005](../adr/0005-satuan-bertingkat.md) |
| K7 | **Stok selalu disimpan dalam satuan dasar.** Konversi terjadi di tepi, bukan tersebar. | [ADR-0005](../adr/0005-satuan-bertingkat.md) |

## Berkas yang dibangun

```
backend/app/
  model/
    kategori.py            tabel kategori
    produk.py              tabel produk dan satuan_produk
    mutasi.py              tabel mutasi_stok
  skema/
    produk.py              bentuk masuk dan keluar
    impor.py               bentuk hasil pratinjau impor
  layanan/
    satuan.py              konversi satuan, penjagaan faktor
    stok.py                menulis mutasi, menghitung saldo, kartu stok
    produk.py              CRUD produk, satuan, kategori
    impor.py               baca CSV, periksa baris, simpan
  rute/
    produk.py
    kategori.py
    stok.py

frontend/src/fitur/
  produk/                  daftar, form, pengelolaan satuan
  impor/                   unggah CSV dan pratinjau
```

---

## Tugas 1: Model kategori, produk, dan satuan

**Berkas:** `app/model/kategori.py`, `app/model/produk.py`, migrasi
**Uji:** `tests/test_model_produk.py`

**Antarmuka yang dihasilkan:**
- `Kategori(id, nama, diubah_pada)`
- `Produk(id, kode, nama, kategori_id, satuan_dasar, stok, stok_minimum, hpp, perlu_dilengkapi, uuid_klien, aktif)`
- `SatuanProduk(id, produk_id, nama, faktor, harga_jual, barcode, is_dasar, aktif)`

- [ ] **Langkah 1: Tulis model**

```python
# app/model/kategori.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.model.dasar import Dasar, KolomWaktu


class Kategori(Dasar, KolomWaktu):
    __tablename__ = "kategori"

    id: Mapped[int] = mapped_column(primary_key=True)
    nama: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
```

```python
# app/model/produk.py
from decimal import Decimal
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.dasar import Dasar, KolomWaktu

JUMLAH = Numeric(14, 3)   # ketelitian sampai satu gram
TARIF = Numeric(14, 4)    # HPP: tarif turunan, bukan jumlah yang dibayar


class Produk(Dasar, KolomWaktu):
    __tablename__ = "produk"

    id: Mapped[int] = mapped_column(primary_key=True)
    kode: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    nama: Mapped[str] = mapped_column(String(150), nullable=False)
    kategori_id: Mapped[int | None] = mapped_column(ForeignKey("kategori.id"))
    satuan_dasar: Mapped[str] = mapped_column(String(20), nullable=False)
    stok: Mapped[Decimal] = mapped_column(JUMLAH, default=Decimal("0"), nullable=False)
    stok_minimum: Mapped[Decimal] = mapped_column(JUMLAH, default=Decimal("0"), nullable=False)
    hpp: Mapped[Decimal] = mapped_column(TARIF, default=Decimal("0"), nullable=False)
    perlu_dilengkapi: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    uuid_klien: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), unique=True)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    satuan: Mapped[list["SatuanProduk"]] = relationship(
        back_populates="produk", cascade="all, delete-orphan", lazy="selectin"
    )


class SatuanProduk(Dasar, KolomWaktu):
    __tablename__ = "satuan_produk"
    __table_args__ = (
        UniqueConstraint("produk_id", "nama", name="uq_satuan_produk_nama"),
        CheckConstraint("faktor > 0", name="ck_satuan_faktor_positif"),
        CheckConstraint("harga_jual >= 0", name="ck_satuan_harga_tak_negatif"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    produk_id: Mapped[int] = mapped_column(ForeignKey("produk.id"), index=True)
    nama: Mapped[str] = mapped_column(String(20), nullable=False)
    faktor: Mapped[Decimal] = mapped_column(JUMLAH, nullable=False)
    harga_jual: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(32), unique=True)
    is_dasar: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    produk: Mapped[Produk] = relationship(back_populates="satuan")
```

`CheckConstraint` ditaruh di basis data, bukan hanya di Python, karena ia lapis terakhir yang tidak bisa dilewati bug di lapis mana pun ([bab 09 §9.2](../perancangan/09-penanganan-error.md)).

- [ ] **Langkah 2: Daftarkan di `migrasi/env.py`, bangkitkan, terapkan, rapikan**

```bash
uv run alembic revision --autogenerate -m "tabel kategori, produk, satuan"
uv run alembic upgrade head
uv run ruff format migrasi/versions && uv run ruff check --fix migrasi
```

- [ ] **Langkah 3: Uji**

```python
# tests/test_model_produk.py
import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.model.produk import Produk, SatuanProduk


def produk_baru(sesi: Session, kode: str = "P001") -> Produk:
    p = Produk(kode=kode, nama="Indomie Goreng", satuan_dasar="bungkus")
    sesi.add(p)
    sesi.commit()
    return p


def test_jumlah_menyimpan_tiga_angka_desimal(sesi: Session) -> None:
    p = produk_baru(sesi)
    p.stok = Decimal("1.500")
    sesi.commit()
    sesi.refresh(p)
    assert p.stok == Decimal("1.500")


def test_hpp_menyimpan_empat_angka_desimal(sesi: Session) -> None:
    p = produk_baru(sesi)
    p.hpp = Decimal("2866.6667")
    sesi.commit()
    sesi.refresh(p)
    assert p.hpp == Decimal("2866.6667")


def test_faktor_nol_ditolak_basis_data(sesi: Session) -> None:
    p = produk_baru(sesi)
    sesi.add(SatuanProduk(produk_id=p.id, nama="dus", faktor=Decimal("0"), harga_jual=1))
    with pytest.raises(IntegrityError):
        sesi.commit()


def test_barcode_wajib_unik_lintas_produk(sesi: Session) -> None:
    a = produk_baru(sesi, "P001")
    b = produk_baru(sesi, "P002")
    sesi.add(SatuanProduk(produk_id=a.id, nama="bungkus", faktor=Decimal("1"),
                          harga_jual=3500, barcode="899100", is_dasar=True))
    sesi.commit()
    sesi.add(SatuanProduk(produk_id=b.id, nama="bungkus", faktor=Decimal("1"),
                          harga_jual=3000, barcode="899100", is_dasar=True))
    with pytest.raises(IntegrityError):
        sesi.commit()


def test_nama_satuan_unik_dalam_satu_produk(sesi: Session) -> None:
    p = produk_baru(sesi)
    for _ in range(2):
        sesi.add(SatuanProduk(produk_id=p.id, nama="dus", faktor=Decimal("40"), harga_jual=1))
    with pytest.raises(IntegrityError):
        sesi.commit()
```

- [ ] **Langkah 4: Commit**

---

## Tugas 2: Konversi satuan

**Berkas:** `app/layanan/satuan.py` · **Uji:** `tests/test_satuan.py`

**Antarmuka yang dihasilkan:**
- `ke_satuan_dasar(jumlah: Decimal, faktor: Decimal) -> Decimal`
- `satuan_dasar_dari(produk: Produk) -> SatuanProduk`
- `periksa_satuan(daftar: list[SatuanProduk]) -> None` melempar `KesalahanDomain` bila melanggar

- [ ] **Langkah 1: Tulis layanan**

```python
from decimal import Decimal

from app.kesalahan import KesalahanDomain
from app.model.produk import Produk, SatuanProduk


def ke_satuan_dasar(jumlah: Decimal, faktor: Decimal) -> Decimal:
    """Mengubah jumlah dalam satuan terpilih menjadi jumlah satuan dasar.

    Satu-satunya tempat perkalian ini terjadi. Menyebarnya ke banyak
    tempat adalah cara paling pasti membuat stok berselisih.
    """
    return jumlah * faktor


def satuan_dasar_dari(produk: Produk) -> SatuanProduk:
    for s in produk.satuan:
        if s.is_dasar:
            return s
    raise KesalahanDomain(
        "SATUAN_DASAR_TIDAK_ADA",
        f"Produk {produk.nama} belum punya satuan dasar",
    )


def periksa_satuan(daftar: list[SatuanProduk]) -> None:
    dasar = [s for s in daftar if s.is_dasar]
    if len(dasar) != 1:
        raise KesalahanDomain(
            "SATUAN_DASAR_TUNGGAL",
            f"Produk harus punya tepat satu satuan dasar, ditemukan {len(dasar)}",
        )
    if dasar[0].faktor != Decimal("1"):
        raise KesalahanDomain(
            "FAKTOR_DASAR_HARUS_SATU",
            "Satuan dasar harus berfaktor 1, karena ia yang menjadi acuan",
        )
    for s in daftar:
        if s.faktor <= 0:
            raise KesalahanDomain(
                "SATUAN_FAKTOR_TIDAK_SAH",
                "Faktor satuan harus lebih besar dari 0",
                detail={"satuan": s.nama},
            )
```

- [ ] **Langkah 2: Uji, termasuk uji properti**

Angka pada uji berikut diambil dari [bab 03 §3.5](../perancangan/03-model-data.md#35-contoh-terhitung), bukan dari keluaran program.

```python
from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from app.kesalahan import KesalahanDomain
from app.layanan.satuan import ke_satuan_dasar, periksa_satuan
from app.model.produk import SatuanProduk


def satuan(nama: str, faktor: str, dasar: bool = False) -> SatuanProduk:
    return SatuanProduk(nama=nama, faktor=Decimal(faktor), harga_jual=1, is_dasar=dasar)


def test_satu_dus_menjadi_empat_puluh_bungkus() -> None:
    assert ke_satuan_dasar(Decimal("1"), Decimal("40")) == Decimal("40")


def test_barang_curah_berdesimal() -> None:
    assert ke_satuan_dasar(Decimal("1.5"), Decimal("1")) == Decimal("1.5")


def test_satuan_dasar_wajib_tepat_satu() -> None:
    with pytest.raises(KesalahanDomain) as e:
        periksa_satuan([satuan("bungkus", "1", True), satuan("dus", "40", True)])
    assert e.value.kode == "SATUAN_DASAR_TUNGGAL"


def test_satuan_dasar_wajib_berfaktor_satu() -> None:
    with pytest.raises(KesalahanDomain) as e:
        periksa_satuan([satuan("dus", "40", True)])
    assert e.value.kode == "FAKTOR_DASAR_HARUS_SATU"


@given(
    jumlah=st.decimals(min_value=Decimal("0.001"), max_value=Decimal("9999"), places=3),
    faktor=st.decimals(min_value=Decimal("0.001"), max_value=Decimal("1000"), places=3),
)
def test_konversi_bolak_balik_kembali_ke_asal(jumlah: Decimal, faktor: Decimal) -> None:
    """Sifat yang harus selalu benar, bukan sekadar untuk contoh yang dipilih."""
    assert ke_satuan_dasar(jumlah, faktor) / faktor == jumlah
```

- [ ] **Langkah 3: Commit**

---

## Tugas 3: Buku besar stok

**Berkas:** `app/model/mutasi.py`, `app/layanan/stok.py` · **Uji:** `tests/test_stok.py`

**Antarmuka yang dihasilkan:**
- `TipeMutasi` (enum: `stok_awal`, `penjualan`, `retur_penjualan`, `pembelian`, `retur_pembelian`, `penyesuaian`, `opname`)
- `catat_mutasi(sesi, produk_id, tipe, jumlah_dasar, pengguna_id, alasan=None, rujukan_tipe=None, rujukan_id=None) -> MutasiStok`
- `kartu_stok(sesi, produk_id) -> list[MutasiStok]`
- `periksa_keselarasan(sesi) -> list[tuple[int, Decimal, Decimal]]`

- [ ] **Langkah 1: Tulis model dan layanan**

Inti yang tidak boleh salah, dan alasannya:

```python
def catat_mutasi(...) -> MutasiStok:
    # Baris produk dikunci lebih dulu. Tanpa ini, dua mutasi yang tiba
    # bersamaan membaca saldo yang sama dan menulis saldo_sesudah yang
    # keliru (bab 03 aturan integritas #2).
    produk = sesi.execute(
        select(Produk).where(Produk.id == produk_id).with_for_update()
    ).scalar_one()

    if tipe is TipeMutasi.penyesuaian and not alasan:
        raise KesalahanDomain("ALASAN_WAJIB", "Penyesuaian stok harus disertai alasan")

    saldo_baru = produk.stok + jumlah_dasar
    mutasi = MutasiStok(
        produk_id=produk.id, tipe=tipe, jumlah=jumlah_dasar,
        saldo_sesudah=saldo_baru, hpp_saat_itu=produk.hpp,
        alasan=alasan, rujukan_tipe=rujukan_tipe, rujukan_id=rujukan_id,
        pengguna_id=pengguna_id,
    )
    sesi.add(mutasi)
    produk.stok = saldo_baru          # salinan cepat, ditulis di transaksi yang sama
    return mutasi
```

Stok yang menjadi negatif **tidak** dihalangi ([ADR-0006](../adr/0006-stok-boleh-minus.md)). Yang dilakukan hanyalah mencatat, dan pemilik melihatnya lewat laporan stok minus.

- [ ] **Langkah 2: Uji**

Kasus wajib:

| Uji | Yang dijaga |
|---|---|
| `saldo_sesudah` berurutan setelah tiga mutasi | K3 |
| `produk.stok` sama dengan jumlah seluruh mutasi | K3 |
| Penyesuaian tanpa alasan ditolak | Bab 04 |
| Stok boleh menjadi negatif | K5 |
| Kartu stok mengembalikan seluruh mutasi berurutan waktu | Bab 04 |
| `periksa_keselarasan` mengembalikan kosong saat sehat | K3 |
| Dua mutasi bersamaan menghasilkan saldo berurutan, bukan tertimpa | Bab 03 #2 |

- [ ] **Langkah 3: Commit**

---

## Tugas 4: Layanan produk

**Berkas:** `app/layanan/produk.py`, `app/skema/produk.py` · **Uji:** `tests/test_produk.py`

**Antarmuka yang dihasilkan:**
- `buat_produk(sesi, data, pengguna_id) -> Produk`, membuat produk berikut satuannya, dan bila `stok_awal` terisi, satu mutasi bertipe `stok_awal`
- `ubah_produk(sesi, produk_id, data) -> Produk`
- `cari_produk(sesi, kata: str, batas: int = 50) -> list[Produk]`
- `tambah_cepat(sesi, nama, harga, pengguna_id, uuid_klien=None) -> Produk`

Urutan pencarian mengikuti [bab 04 §4.1](../perancangan/04-alur-kerja.md#41-kasir-satu-hari-kerja): barcode persis, lalu kode persis, lalu nama mengandung kata kunci.

- [ ] **Langkah 1: Tulis layanan** dengan penjagaan: kode unik, `periksa_satuan` dipanggil sebelum simpan, harga tiap satuan ditulis sendiri (K6).
- [ ] **Langkah 2: Uji**, termasuk contoh terhitung dari bab 03 §3.5.
- [ ] **Langkah 3: Commit**

---

## Tugas 5: Endpoint katalog

**Berkas:** `app/rute/kategori.py`, `app/rute/produk.py`, `app/rute/stok.py`

| Metode | Jalur | Peran |
|---|---|---|
| GET POST PATCH | `/kategori` | pemilik |
| GET | `/produk?cari=&kategori_id=&aktif=&perlu_dilengkapi=` | keduanya |
| POST PATCH | `/produk` | pemilik |
| POST | `/produk/kilat` | keduanya |
| POST PATCH | `/produk/{id}/satuan`, `/satuan/{id}` | pemilik |
| GET | `/produk/{id}/kartu-stok` | pemilik |
| POST | `/penyesuaian-stok` | pemilik |
| GET | `/stok/menipis`, `/stok/minus` | pemilik |

**Kolom `hpp` disaring untuk peran kasir**, di endpoint ini maupun di sinkronisasi kelak ([bab 08 §8.1](../perancangan/08-keamanan-dan-peran.md#81-dua-peran)). Uji integrasi wajib memastikannya.

- [ ] Tulis rute tipis tanpa aturan bisnis, uji hak akses dan penyaringan `hpp`, commit.

---

## Tugas 6: Impor CSV

**Berkas:** `app/layanan/impor.py`, `app/skema/impor.py` · **Uji:** `tests/test_impor.py`

Tanpa keadaan sementara di server: pratinjau memeriksa lalu melupakan, dan berkas dikirim ulang saat dijalankan ([bab 07 §7.4](../perancangan/07-kontrak-api.md)).

Kolom CSV: `kode, nama, kategori, satuan_dasar, harga_jual, barcode, stok_awal, stok_minimum`.

Kegagalan dilaporkan **per baris dengan nomor barisnya**, bukan sebagai satu pesan gagal. Baris yang sah tetap bisa dilanjutkan tanpa yang gagal.

- [ ] Tulis layanan, uji baris rusak menyebut nomor baris yang benar, commit.

---

## Tugas 7 sampai 9: Frontend katalog

- **Tugas 7:** Layar daftar produk, pencarian seketika, penanda stok menipis dan stok minus.
- **Tugas 8:** Form produk berikut pengelolaan satuan, dengan aturan tepat satu satuan dasar ditegakkan juga di tampilan.
- **Tugas 9:** Layar impor CSV: unggah, pratinjau berikut daftar baris gagal, lalu jalankan.

Tipe dibangkitkan ulang dengan `npm run tipe` setiap kali bentuk data di server berubah.

---

## Tugas 10: Pemeriksaan M1 ujung-ke-ujung

- [ ] Basis data dari nol, migrasi, impor CSV berisi 30 produk contoh termasuk yang bersatuan ganda dan barang curah.
- [ ] Buat produk bersatuan `bungkus` dan `dus` berfaktor 40, pastikan menjual satu dus mengurangi 40 bungkus lewat penyesuaian.
- [ ] Pastikan `periksa_keselarasan` mengembalikan kosong setelah seluruh langkah di atas.
- [ ] Pastikan akun kasir tidak menerima kolom `hpp` di jawaban mana pun.
- [ ] `npm run build:www`, buka `http://localhost/toko`, telusuri daftar produk.

**M1 selesai** ketika kelima langkah ini lulus dan CI hijau.
