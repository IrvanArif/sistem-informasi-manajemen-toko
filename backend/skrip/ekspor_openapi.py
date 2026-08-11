"""Menulis skema OpenAPI ke berkas, untuk membangkitkan tipe TypeScript.

Skema dibaca langsung dari objek aplikasi, bukan lewat HTTP. Karena itu
perintah ini tetap bekerja meski endpoint /openapi.json ditutup di
produksi (bab 08).
"""

import json
from pathlib import Path

from app.main import buat_aplikasi

BERKAS = Path(__file__).parent.parent / "openapi.json"


def main() -> None:
    spek = buat_aplikasi().openapi()
    BERKAS.write_text(json.dumps(spek, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OpenAPI ditulis ke {BERKAS} ({len(spek['paths'])} jalur)")


if __name__ == "__main__":
    main()
