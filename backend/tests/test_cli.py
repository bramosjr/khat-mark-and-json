import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

import cli

BACKEND = Path(__file__).resolve().parent.parent


def _run(*argv):
    out, err = io.StringIO(), io.StringIO()
    code = cli.main(list(argv), stdin=io.StringIO(""), stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def _csv(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("a,b\n1,2\n")
    return str(p)


def test_convert_humano_imprime_markdown(tmp_path):
    code, out, err = _run("convert", _csv(tmp_path))
    assert code == 0 and "| a | b |" in out and err == ""


def test_convert_json_flag_imprime_envelope(tmp_path):
    code, out, _ = _run("convert", _csv(tmp_path), "--formato", "json", "--json")
    assert code == 0
    env = json.loads(out)
    assert env["ok"] is True and env["conteudo"]["metadata"]["rows"] == 1


def test_erro_em_modo_json_e_estruturado(tmp_path):
    code, out, _ = _run("convert", str(tmp_path / "x.csv"), "--json")
    assert code == 1
    assert json.loads(out) == {"erro": json.loads(out)["erro"], "codigo": "ARQUIVO_NAO_ENCONTRADO"}


def test_erro_em_modo_humano_vai_para_stderr(tmp_path):
    code, out, err = _run("convert", str(tmp_path / "x.csv"))
    assert code == 1 and out == "" and "ARQUIVO_NAO_ENCONTRADO" in err


def test_dry_run_nao_grava(tmp_path):
    destino = tmp_path / "o.md"
    code, out, _ = _run("convert", _csv(tmp_path), "--saida", str(destino), "--dry-run", "--json")
    assert code == 0 and json.loads(out)["dry_run"] is True and not destino.exists()


def test_saida_grava_e_confirma(tmp_path):
    destino = tmp_path / "o.md"
    code, out, _ = _run("convert", _csv(tmp_path), "--saida", str(destino), "--json")
    assert code == 0 and destino.exists() and json.loads(out)["saida"] == str(destino.resolve())


def test_confinamento_na_cli(tmp_path):
    raiz = tmp_path / "raiz"
    raiz.mkdir()
    code, out, _ = _run("convert", _csv(tmp_path), "--json", "--automation-read-root", str(raiz),
                        "--automation-write-root", str(raiz))
    assert code == 1 and json.loads(out)["codigo"] == "CAMINHO_RECUSADO"


def test_describe_lista_comandos_ferramentas_e_codigos_de_saida():
    code, out, _ = _run("describe")
    assert code == 0
    d = json.loads(out)
    assert {"convert", "describe", "mcp"} <= {c["nome"] for c in d["comandos"]}
    assert {t["name"] for t in d["ferramentas_mcp"]} == {"inspecionar", "executar"}
    assert set(d["codigos_saida"]) == {"0", "1", "2"}


def test_schema_e_alias_de_describe():
    assert _run("--schema") == _run("describe")


@pytest.mark.parametrize("argv", [
    [], ["inexistente"], ["convert"], ["convert", "a.csv", "--formato", "xml"],
    ["convert", "a.csv", "--flag-estranha"], ["convert", "a.csv", "--automation-read-rot", "x"],
    ["convert", "a.csv", "--connect", "9"],
])
def test_uso_incorreto_retorna_2(argv):
    code, out, err = _run(*argv)
    assert code == 2 and err.strip() != ""


def test_main_py_com_argumentos_despacha_para_a_cli():
    p = subprocess.run([sys.executable, str(BACKEND / "main.py"), "describe"],
                       capture_output=True, text=True, cwd=str(BACKEND), timeout=60)
    assert p.returncode == 0 and "comandos" in json.loads(p.stdout)
