"""Servidor MCP (stdio, JSON-RPC 2.0 delimitado por \\n). Somente stdlib.

Erros de protocolo (JSON inválido, método inexistente) usam o campo `error`;
erros de domínio voltam como `result` com `isError: true`, para o agente ler
a causa e corrigir a chamada. Nada além do JSON-RPC pode ir para o stdout.
"""
import json
import os
import sys
from typing import Any, Dict, Optional, TextIO

from core.automation import APP_NAME, TOOLS, Automation, AutomationError

SUPPORTED_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"]
PRIMARY_VERSION = SUPPORTED_VERSIONS[0]


def isolate_stdout() -> TextIO:
    """Reserva o stdout real só para o protocolo.

    Duplica o fd 1 e aponta o fd 1 para o stderr, para que `print()`, avisos de
    bibliotecas e subprocessos nunca corrompam o JSON-RPC.
    """
    try:
        sys.stdout.flush()
    except Exception:
        pass
    proto_fd = os.dup(1)
    os.dup2(2, 1)
    sys.stdout = sys.stderr
    return os.fdopen(proto_fd, "w", encoding="utf-8", newline="\n", buffering=1)


def _ok(req_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _tool_result(payload: Dict[str, Any], is_error: bool) -> Dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
            "isError": is_error}


class McpServer:
    def __init__(self, automation: Automation, version: str = "0.0.0"):
        self.automation = automation
        self.version = version

    def _instructions(self) -> str:
        c = self.automation.confinement
        texto = ("Khat Mark And Json: converte documentos locais para Markdown ou JSON, 100% offline.\n"
                 "Backend: headless engine.")
        if c.enabled:
            texto += (f"\nArquivos confinados: raiz de leitura {c.read_root or 'nenhuma'}, "
                      f"raiz de escrita {c.write_root or 'nenhuma'}.")
        return texto

    def handle(self, req: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(req, dict):
            return _err(None, -32600, "invalid request: esperado um objeto JSON")
        req_id = req.get("id")
        method = req.get("method")
        if req_id is None:
            return None  # notificações não recebem resposta
        params = req.get("params")
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return _err(req_id, -32602, "invalid params: esperado um objeto")

        if method == "initialize":
            want = params.get("protocolVersion")
            return _ok(req_id, {
                "protocolVersion": want if want in SUPPORTED_VERSIONS else PRIMARY_VERSION,
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": APP_NAME, "version": self.version},
                "instructions": self._instructions(),
            })
        if method == "ping":
            return _ok(req_id, {})
        if method == "tools/list":
            return _ok(req_id, {"tools": TOOLS})
        if method == "tools/call":
            return _ok(req_id, self._call_tool(params.get("name"), params.get("arguments")))
        return _err(req_id, -32601, f"method not found: {method}")

    def _call_tool(self, name: Any, arguments: Any) -> Dict[str, Any]:
        try:
            return _tool_result(self.automation.chamar(str(name), arguments), False)
        except AutomationError as e:
            return _tool_result(e.to_dict(), True)
        except Exception as e:  # nunca derruba o servidor por causa de uma chamada
            return _tool_result({"erro": f"{type(e).__name__}: {e}", "codigo": "ERRO_INTERNO"}, True)

    def serve(self, stdin: TextIO, stdout: TextIO, stderr: Optional[TextIO] = None) -> None:
        stderr = stderr or sys.stderr
        c = self.automation.confinement
        if c.enabled:
            stderr.write(f"{APP_NAME}: files confined: read root {c.read_root or 'none'}, "
                         f"write root {c.write_root or 'none'}\n")
            stderr.flush()
        for line in stdin:
            line = line.strip()
            if not line:
                continue
            try:
                resp = self.handle(json.loads(line))
            except json.JSONDecodeError as e:
                resp = _err(None, -32700, f"parse error: {e}")
            if resp is not None:
                stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                stdout.flush()
