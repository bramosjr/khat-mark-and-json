"""CLI humana e servidor MCP do Khat Mark And Json (camada fina sobre o núcleo).

Uso:
  markitdown-backend convert ARQUIVO [--formato md|json] [--saida X] [--json] [--dry-run]
  markitdown-backend describe | --schema
  markitdown-backend mcp [--automation-read-root DIR] [--automation-write-root DIR]

Sem argumentos o backend sobe o servidor HTTP da GUI (ver main.py).
Códigos de saída: 0 sucesso; 1 erro de negócio; 2 uso/argumento inválido.
"""
import argparse
import json
import sys
from typing import List, Optional, Tuple

from core.automation import (
    APP_NAME, DEFAULT_MAX_CHARS, DEFAULT_MAX_INPUT_BYTES, FORMATS, TOOLS,
    Automation, AutomationError, _read_version_info,
)
from core.confinement import Confinement
from core.mcp_server import PRIMARY_VERSION, SUPPORTED_VERSIONS, McpServer, isolate_stdout

EXIT_OK, EXIT_ERROR, EXIT_USAGE = 0, 1, 2

CODIGOS_ERRO = [
    "ENTRADA_INVALIDA", "ARQUIVO_NAO_ENCONTRADO", "EXTENSAO_NAO_SUPORTADA", "ARQUIVO_GRANDE",
    "CAMINHO_RECUSADO", "SAIDA_EXISTE", "CONTEUDO_GRANDE", "CONVERSAO_FALHOU", "ERRO_DE_ESCRITA",
]


class UsageError(Exception):
    pass


def split_automation_args(args: List[str]) -> Tuple[Optional[str], Optional[str], int, List[str]]:
    """Extrai as flags de automação (fail-closed) e devolve o restante.

    Qualquer `--automation-*` desconhecida ou sem valor aborta: o processo nunca
    deve subir desconfinado por engano de digitação. `--connect` é recusado.
    """
    read_root = write_root = None
    max_mb = DEFAULT_MAX_INPUT_BYTES // (1024 * 1024)
    rest: List[str] = []
    i = 0
    while i < len(args):
        tok = args[i]
        name, eq, inline = tok.partition("=")
        if name == "--connect":
            raise UsageError("--connect não é suportado: não há estado vivo da GUI para espelhar (somente modo headless)")
        if name in ("--automation-read-root", "--automation-write-root", "--max-input-mb"):
            if eq:
                value = inline
            else:
                i += 1
                value = args[i] if i < len(args) else ""
                if value.startswith("--"):
                    value = ""
            if not value:
                raise UsageError(f"{name} exige um valor")
            if name == "--automation-read-root":
                read_root = value
            elif name == "--automation-write-root":
                write_root = value
            else:
                try:
                    max_mb = int(value)
                except ValueError:
                    raise UsageError("--max-input-mb deve ser um inteiro positivo")
                if max_mb < 1:
                    raise UsageError("--max-input-mb deve ser um inteiro positivo")
        elif tok.startswith("--automation-"):
            raise UsageError(f"opção desconhecida `{tok}`")
        else:
            rest.append(tok)
        i += 1
    return read_root, write_root, max_mb, rest


def _build_automation(read_root, write_root, max_mb) -> Automation:
    return Automation(confinement=Confinement(read_root, write_root),
                      max_input_bytes=max_mb * 1024 * 1024)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def describe() -> dict:
    info = _read_version_info()
    return {
        "app": APP_NAME,
        "versao": info.get("app_version"),
        "comandos": [
            {"nome": "convert", "descricao": "Converte um documento local para Markdown ou JSON.",
             "argumentos": ["ARQUIVO", "--formato md|json", "--saida CAMINHO", "--max-chars N",
                            "--sobrescrever", "--dry-run", "--json",
                            "--automation-read-root DIR", "--automation-write-root DIR", "--max-input-mb N"]},
            {"nome": "describe", "descricao": "Lista comandos, ferramentas MCP e códigos de saída (alias: --schema).",
             "argumentos": []},
            {"nome": "mcp", "descricao": "Servidor MCP em stdio (JSON-RPC 2.0), somente modo headless.",
             "argumentos": ["--automation-read-root DIR", "--automation-write-root DIR", "--max-input-mb N"]},
        ],
        "ferramentas_mcp": TOOLS,
        "protocolo_mcp": {"versoes": SUPPORTED_VERSIONS, "preferida": PRIMARY_VERSION},
        "codigos_saida": {"0": "sucesso", "1": "erro de negócio (ver 'codigo' no JSON de erro)",
                          "2": "uso incorreto ou argumento inválido"},
        "codigos_erro": CODIGOS_ERRO,
        "formatos": list(FORMATS),
    }


def _cmd_convert(args: List[str], stdout, stderr) -> int:
    read_root, write_root, max_mb, rest = split_automation_args(args)
    p = _Parser(prog=f"{APP_NAME} convert", add_help=False)
    p.add_argument("arquivo")
    p.add_argument("--formato", choices=FORMATS, default="md")
    p.add_argument("--saida")
    p.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    p.add_argument("--sobrescrever", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true", dest="as_json")
    ns = p.parse_args(rest)
    if ns.max_chars < 1:
        raise UsageError("--max-chars deve ser >= 1")

    automation = _build_automation(read_root, write_root, max_mb)
    try:
        r = automation.executar(ns.arquivo, formato=ns.formato, saida=ns.saida,
                                max_chars=ns.max_chars, sobrescrever=ns.sobrescrever, dry_run=ns.dry_run)
    except AutomationError as e:
        if ns.as_json:
            stdout.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
        else:
            stderr.write(f"erro [{e.codigo}]: {e.mensagem}\n")
        return EXIT_ERROR

    if ns.as_json:
        stdout.write(json.dumps(r, ensure_ascii=False) + "\n")
    elif "conteudo" in r:
        c = r["conteudo"]
        stdout.write((c if isinstance(c, str) else json.dumps(c, ensure_ascii=False, indent=2)) + "\n")
        if r.get("truncado"):
            stderr.write(f"aviso: conteúdo truncado em {ns.max_chars} de {r['caracteres_total']} caracteres "
                         "(use --saida ou --max-chars)\n")
    elif r.get("dry_run"):
        stdout.write(f"[dry-run] converteria {r['arquivo']} ({r['formato']})"
                     + (f" e gravaria em {r['saida']}" if r.get("saida") else "") + "\n")
    else:
        stdout.write(f"gravado em {r['saida']} ({r['caracteres']} caracteres)\n")
    return EXIT_OK


def _cmd_mcp(args: List[str], stdin, stdout, stderr, isolate: bool) -> int:
    read_root, write_root, max_mb, rest = split_automation_args(args)
    if rest:
        raise UsageError(f"argumento inesperado para mcp: {rest[0]}")
    automation = _build_automation(read_root, write_root, max_mb)
    version = _read_version_info().get("app_version") or "0.0.0"
    if isolate:
        try:
            stdin.reconfigure(encoding="utf-8")
        except Exception:
            pass
        stdout = isolate_stdout()
    McpServer(automation, version=version).serve(stdin, stdout, stderr)
    return EXIT_OK


def main(argv: List[str], stdin=None, stdout=None, stderr=None) -> int:
    real_run = stdout is None
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    try:
        if not argv:
            raise UsageError("comando ausente (convert | describe | mcp)")
        cmd, rest = argv[0], argv[1:]
        if cmd in ("describe", "--schema"):
            if rest:
                raise UsageError(f"argumento inesperado para {cmd}: {rest[0]}")
            stdout.write(json.dumps(describe(), ensure_ascii=False, indent=2) + "\n")
            return EXIT_OK
        if cmd == "convert":
            return _cmd_convert(rest, stdout, stderr)
        if cmd == "mcp":
            return _cmd_mcp(rest, stdin, stdout, stderr, isolate=real_run)
        raise UsageError(f"comando desconhecido: {cmd}")
    except UsageError as e:
        stderr.write(f"erro: {e}\nuso: {APP_NAME} convert ARQUIVO [opções] | describe | mcp [opções]\n")
        return EXIT_USAGE
