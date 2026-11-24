import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from core.automation import Automation
from core.mcp_server import McpServer, SUPPORTED_VERSIONS

BACKEND = Path(__file__).resolve().parent.parent
MAIN = str(BACKEND / "main.py")


def _srv():
    return McpServer(Automation())


def _req(method, id=1, **params):
    return {"jsonrpc": "2.0", "id": id, "method": method, "params": params}


def test_initialize_negocia_versao_suportada():
    for v in SUPPORTED_VERSIONS:
        r = _srv().handle(_req("initialize", protocolVersion=v, capabilities={}))
        assert r["result"]["protocolVersion"] == v
    r = _srv().handle(_req("initialize", protocolVersion="1999-01-01"))
    assert r["result"]["protocolVersion"] == "2025-06-18"
    assert SUPPORTED_VERSIONS == ["2025-06-18", "2025-03-26", "2024-11-05"]


def test_initialize_anuncia_capacidades_e_modo_headless():
    res = _srv().handle(_req("initialize", protocolVersion="2025-06-18"))["result"]
    assert res["capabilities"] == {"tools": {}, "resources": {}}
    assert res["serverInfo"]["name"] == "khat-mark-and-json"
    assert "headless" in res["instructions"]


def test_ping():
    assert _srv().handle(_req("ping", id=7)) == {"jsonrpc": "2.0", "id": 7, "result": {}}


def test_tools_list():
    tools = _srv().handle(_req("tools/list"))["result"]["tools"]
    assert {t["name"] for t in tools} == {"inspecionar", "executar"}
    executar = next(t for t in tools if t["name"] == "executar")
    assert executar["inputSchema"]["required"] == ["arquivo"]
    assert set(executar["inputSchema"]["properties"]) >= {
        "arquivo", "formato", "saida", "max_chars", "sobrescrever", "dry_run"}


def test_tools_call_inspecionar():
    r = _srv().handle(_req("tools/call", name="inspecionar", arguments={}))["result"]
    assert r["isError"] is False
    assert json.loads(r["content"][0]["text"])["modo"] == "headless"


def test_tools_call_executar_sucesso(tmp_path):
    csv = tmp_path / "d.csv"
    csv.write_text("a,b\n1,2\n")
    r = _srv().handle(_req("tools/call", name="executar", arguments={"arquivo": str(csv)}))["result"]
    assert r["isError"] is False
    assert "| a | b |" in json.loads(r["content"][0]["text"])["conteudo"]


def test_erro_de_dominio_volta_como_resultado_com_iserror(tmp_path):
    r = _srv().handle(_req("tools/call", name="executar",
                           arguments={"arquivo": str(tmp_path / "x.csv")}))
    assert "error" not in r
    assert r["result"]["isError"] is True
    corpo = json.loads(r["result"]["content"][0]["text"])
    assert corpo["codigo"] == "ARQUIVO_NAO_ENCONTRADO" and "erro" in corpo


def test_argumentos_invalidos_viram_erro_de_ferramenta():
    for args in ({}, {"arquivo": 5}, "texto", {"arquivo": "x", "extra": 1}):
        r = _srv().handle(_req("tools/call", name="executar", arguments=args))["result"]
        assert r["isError"] is True


def test_ferramenta_desconhecida():
    r = _srv().handle(_req("tools/call", name="nada", arguments={}))["result"]
    assert r["isError"] is True


def test_metodo_inexistente_e_erro_de_protocolo():
    r = _srv().handle(_req("foo/bar"))
    assert r["error"]["code"] == -32601


def test_notificacao_nao_recebe_resposta():
    assert _srv().handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


def test_serve_responde_uma_linha_por_mensagem_e_trata_json_invalido():
    entrada = io.StringIO('\n{"jsonrpc":"2.0","id":1,"method":"ping"}\n{quebrado\n[1,2]\n')
    saida = io.StringIO()
    _srv().serve(entrada, saida)
    linhas = [json.loads(l) for l in saida.getvalue().splitlines()]
    assert linhas[0] == {"jsonrpc": "2.0", "id": 1, "result": {}}
    assert linhas[1]["error"]["code"] == -32700 and linhas[1]["id"] is None
    assert linhas[2]["error"]["code"] == -32600


def _run_mcp(args, mensagens, timeout=60):
    entrada = "".join(json.dumps(m) + "\n" for m in mensagens)
    p = subprocess.run([sys.executable, MAIN, "mcp", *args], input=entrada,
                       capture_output=True, text=True, timeout=timeout, cwd=str(BACKEND))
    return p


def test_processo_real_stdout_so_tem_json_rpc(tmp_path):
    csv = tmp_path / "d.csv"
    csv.write_text("a,b\n1,2\n")
    p = _run_mcp([], [
        _req("initialize", id=1, protocolVersion="2025-06-18"),
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        _req("tools/call", id=2, name="executar", arguments={"arquivo": str(csv), "formato": "json"}),
    ])
    assert p.returncode == 0
    linhas = p.stdout.splitlines()
    assert len(linhas) == 2
    assert all(json.loads(l)["jsonrpc"] == "2.0" for l in linhas)


def test_isolate_stdout_manda_ruido_para_stderr():
    codigo = (
        "import os, sys\n"
        "from core.mcp_server import isolate_stdout\n"
        "out = isolate_stdout()\n"
        "print('ruido-python')\n"
        "os.system('echo ruido-subprocesso')\n"
        "out.write('protocolo\\n'); out.flush()\n"
    )
    p = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True,
                       cwd=str(BACKEND), timeout=30)
    assert p.stdout == "protocolo\n"
    assert "ruido-python" in p.stderr and "ruido-subprocesso" in p.stderr


def test_confinamento_via_processo(tmp_path):
    raiz = tmp_path / "raiz"
    raiz.mkdir()
    fora = tmp_path / "fora.csv"
    fora.write_text("a\n1\n")
    p = _run_mcp(["--automation-read-root", str(raiz)], [
        _req("tools/call", id=1, name="executar", arguments={"arquivo": str(fora)}),
    ])
    r = json.loads(p.stdout.splitlines()[0])["result"]
    assert r["isError"] is True and "outside the read root" in r["content"][0]["text"]
    assert "confined" in p.stderr


@pytest.mark.parametrize("args", [
    ["--automation-read-rot", "x"],
    ["--automation-read-root"],
    ["--automation-qualquer"],
    ["--connect", "1234"],
    ["solto"],
    ["--max-input-mb", "abc"],
])
def test_parsing_fail_closed_aborta_com_codigo_2(args):
    p = _run_mcp(args, [])
    assert p.returncode == 2
    assert p.stdout == "" and p.stderr.strip() != ""
