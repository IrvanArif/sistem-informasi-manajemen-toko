from fastapi.testclient import TestClient


def test_sehat_menjawab_sehat(klien: TestClient) -> None:
    jawaban = klien.get("/api/v1/sehat")
    assert jawaban.status_code == 200
    assert jawaban.json() == {"status": "sehat"}
