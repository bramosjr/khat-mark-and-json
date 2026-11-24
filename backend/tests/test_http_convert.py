"""Testes de caracterização da rota POST /api/convert.

Fixam o contrato HTTP consumido pela GUI para que a extração do núcleo
(core/converter.py) não o altere.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("KHAT_TOKEN", raising=False)
    return TestClient(main.app)


def _post(client, name, content, **data):
    return client.post("/api/convert", files={"file": (name, content)}, data=data)


def test_csv_para_markdown(client):
    r = _post(client, "dados.csv", b"a,b\n1,2\n")
    assert r.status_code == 200
    assert set(r.json()) == {"markdown"}
    assert "| a | b |" in r.json()["markdown"]


def test_csv_para_json_usa_parser_tabular_offline(client):
    r = _post(client, "dados.csv", b"nome,idade\nAna,30\nBob,\n", target_format="json")
    assert r.status_code == 200
    data = r.json()["json_data"]
    assert data["metadata"] == {"source_type": "tabular", "rows": 2}
    assert data["content"][1] == {"nome": "Bob", "idade": None}


def test_txt_para_json_vira_documento(client):
    r = _post(client, "nota.txt", b"ola mundo", target_format="json")
    assert r.status_code == 200
    assert r.json()["json_data"] == {"source_type": "document", "content": "ola mundo"}


def test_txt_para_markdown(client):
    r = _post(client, "nota.txt", b"ola mundo")
    assert r.status_code == 200
    assert r.json() == {"markdown": "ola mundo"}


def test_token_exigido_quando_configurado(client, monkeypatch):
    monkeypatch.setenv("KHAT_TOKEN", "segredo")
    assert _post(client, "nota.txt", b"x").status_code == 403
    r = client.post(
        "/api/convert",
        files={"file": ("nota.txt", b"x")},
        headers={"Authorization": "Bearer segredo"},
    )
    assert r.status_code == 200


def test_arquivo_corrompido_vira_500_com_detalhe(client):
    r = _post(client, "quebrado.xlsx", b"isso nao e um xlsx", target_format="json")
    assert r.status_code == 500
    assert "detail" in r.json()


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}
