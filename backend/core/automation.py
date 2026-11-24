"""Camada de automação (CLI e MCP) sobre o núcleo de conversão.

Só stdlib no topo; o conversor (pandas, markitdown) é importado sob demanda.
100% offline: nenhuma chamada de rede e nenhum LLM nesta interface.
"""
import json
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, Optional

from core.confinement import Confinement, ConfinementError

APP_NAME = "khat-mark-and-json"
DEFAULT_MAX_CHARS = 200_000
DEFAULT_MAX_INPUT_BYTES = 50 * 1024 * 1024
FORMATS = ("md", "json")
# .zip fica de fora de propósito (zip bomb) e imagens/áudio exigem LLM.
SUPPORTED_EXTENSIONS = (
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".csv", ".ods", ".odt",
    ".html", ".htm", ".xml", ".json", ".txt", ".md", ".epub", ".msg",
)

TOOLS = [
    {
        "name": "inspecionar",
        "description": (
            "Retorna o estado da aplicação: versões, extensões suportadas, modo de backend, "
            "confinamento de arquivos ativo e limites. Somente leitura."),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "executar",
        "description": (
            "Converte um documento local para Markdown ('md') ou JSON estruturado ('json'), "
            "100% offline. Sem 'saida', devolve o conteúdo na resposta (Markdown maior que "
            "max_chars é truncado; JSON maior que max_chars exige 'saida'). Com 'saida', grava o "
            "arquivo e não devolve o conteúdo. 'dry_run' valida tudo sem converter nem gravar."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "arquivo": {"type": "string", "description": "Caminho do documento de entrada."},
                "formato": {"type": "string", "enum": list(FORMATS), "description": "Formato de saída (padrão: md)."},
                "saida": {"type": "string", "description": "Caminho do arquivo de saída (opcional)."},
                "max_chars": {"type": "integer", "minimum": 1,
                              "description": f"Máximo de caracteres devolvidos inline (padrão {DEFAULT_MAX_CHARS})."},
                "sobrescrever": {"type": "boolean", "description": "Permite sobrescrever 'saida' se já existir."},
                "dry_run": {"type": "boolean", "description": "Só valida e mostra o plano."},
            },
            "required": ["arquivo"],
            "additionalProperties": False,
        },
    },
]


class AutomationError(Exception):
    """Erro de domínio, com código estável para o agente corrigir a chamada."""

    def __init__(self, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem

    def to_dict(self) -> Dict[str, str]:
        return {"erro": self.mensagem, "codigo": self.codigo}


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    return True


def validar_argumentos(nome: str, args: Any) -> Dict[str, Any]:
    tool = next((t for t in TOOLS if t["name"] == nome), None)
    if tool is None:
        raise AutomationError("FERRAMENTA_DESCONHECIDA", f"ferramenta desconhecida: {nome}")
    schema = tool["inputSchema"]
    if args is None:
        args = {}
    if not isinstance(args, dict):
        raise AutomationError("ENTRADA_INVALIDA", "arguments deve ser um objeto JSON")
    props = schema["properties"]
    for key in args:
        if key not in props:
            raise AutomationError("ENTRADA_INVALIDA", f"parâmetro desconhecido: {key}")
    for key in schema.get("required", []):
        if key not in args:
            raise AutomationError("ENTRADA_INVALIDA", f"parâmetro obrigatório ausente: {key}")
    for key, value in args.items():
        spec = props[key]
        if not _type_ok(value, spec["type"]):
            raise AutomationError("ENTRADA_INVALIDA", f"parâmetro '{key}' deve ser {spec['type']}")
        if "enum" in spec and value not in spec["enum"]:
            raise AutomationError("ENTRADA_INVALIDA", f"parâmetro '{key}' deve ser um de {spec['enum']}")
        if "minimum" in spec and value < spec["minimum"]:
            raise AutomationError("ENTRADA_INVALIDA", f"parâmetro '{key}' deve ser >= {spec['minimum']}")
    return args


def _read_version_info() -> Dict[str, Any]:
    if getattr(sys, "frozen", False):
        path = Path(sys.executable).resolve().parent / "version-info.json"
    else:
        path = Path(__file__).resolve().parent.parent / "dist" / "version-info.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _package_version(name: str) -> Optional[str]:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


class Automation:
    def __init__(self, confinement: Optional[Confinement] = None,
                 max_input_bytes: int = DEFAULT_MAX_INPUT_BYTES):
        self.confinement = confinement or Confinement(None, None)
        self.max_input_bytes = max_input_bytes

    # ----- ferramentas -------------------------------------------------
    def chamar(self, nome: str, args: Any) -> Dict[str, Any]:
        args = validar_argumentos(nome, args)
        if nome == "inspecionar":
            return self.inspecionar()
        return self.executar(**args)

    def inspecionar(self) -> Dict[str, Any]:
        info = _read_version_info()
        c = self.confinement
        return {
            "app": APP_NAME,
            "modo": "headless",
            "offline": True,
            "extensoes": list(SUPPORTED_EXTENSIONS),
            "formatos": list(FORMATS),
            "confinamento": {
                "ativo": c.enabled,
                "raiz_leitura": str(c.read_root) if c.read_root else None,
                "raiz_escrita": str(c.write_root) if c.write_root else None,
            },
            "limites": {"max_entrada_bytes": self.max_input_bytes, "max_chars": DEFAULT_MAX_CHARS},
            "versoes": {
                "app": info.get("app_version"),
                "markitdown": info.get("markitdown_version") or _package_version("markitdown"),
                "bibliotecas": info.get("libraries", {}),
            },
        }

    def executar(self, arquivo: str, formato: str = "md", saida: Optional[str] = None,
                 max_chars: int = DEFAULT_MAX_CHARS, sobrescrever: bool = False,
                 dry_run: bool = False) -> Dict[str, Any]:
        if formato not in FORMATS:
            raise AutomationError("ENTRADA_INVALIDA", f"formato deve ser um de {list(FORMATS)}")
        if not isinstance(max_chars, int) or isinstance(max_chars, bool) or max_chars < 1:
            raise AutomationError("ENTRADA_INVALIDA", "max_chars deve ser um inteiro >= 1")
        if not isinstance(arquivo, str) or not arquivo.strip():
            raise AutomationError("ENTRADA_INVALIDA", "arquivo deve ser um caminho não vazio")

        origem = self._validar_entrada(arquivo)
        destino = self._validar_saida(saida, origem, sobrescrever) if saida is not None else None

        if dry_run:
            return {"ok": True, "dry_run": True, "arquivo": str(origem), "formato": formato,
                    "saida": str(destino) if destino else None,
                    "bytes_entrada": origem.stat().st_size}

        from core.converter import build_markitdown, convert_file
        try:
            md = build_markitdown(None, None, None, None)
            resultado = convert_file(str(origem), formato, md)
        except Exception as e:  # erro do motor: o agente precisa ler a causa
            raise AutomationError("CONVERSAO_FALHOU", f"{type(e).__name__}: {e}") from e

        conteudo = resultado["markdown"] if formato == "md" else resultado["json_data"]
        if destino is not None:
            texto = conteudo if formato == "md" else json.dumps(conteudo, ensure_ascii=False, indent=2)
            self._gravar(destino, texto, sobrescrever)
            return {"ok": True, "arquivo": str(origem), "formato": formato,
                    "saida": str(destino), "caracteres": len(texto)}

        if formato == "md":
            truncado = len(conteudo) > max_chars
            return {"ok": True, "arquivo": str(origem), "formato": "md",
                    "conteudo": conteudo[:max_chars] if truncado else conteudo,
                    "truncado": truncado, "caracteres_total": len(conteudo)}

        tamanho = len(json.dumps(conteudo, ensure_ascii=False))
        if tamanho > max_chars:
            raise AutomationError(
                "CONTEUDO_GRANDE",
                f"o JSON tem {tamanho} caracteres (> max_chars={max_chars}); informe 'saida' para gravar em arquivo")
        return {"ok": True, "arquivo": str(origem), "formato": "json",
                "conteudo": conteudo, "truncado": False, "caracteres_total": tamanho}

    # ----- validações --------------------------------------------------
    def _validar_entrada(self, arquivo: str) -> Path:
        try:
            origem = self.confinement.check_read(arquivo)
        except ConfinementError as e:
            raise AutomationError("CAMINHO_RECUSADO", str(e)) from e
        if not origem.is_file():
            raise AutomationError("ARQUIVO_NAO_ENCONTRADO", f"arquivo não encontrado: {arquivo}")
        ext = origem.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise AutomationError(
                "EXTENSAO_NAO_SUPORTADA",
                f"extensão não suportada: '{ext}'. Suportadas: {', '.join(SUPPORTED_EXTENSIONS)}")
        tamanho = origem.stat().st_size
        if tamanho > self.max_input_bytes:
            raise AutomationError(
                "ARQUIVO_GRANDE", f"arquivo com {tamanho} bytes excede o limite de {self.max_input_bytes}")
        return origem

    def _validar_saida(self, saida: str, origem: Path, sobrescrever: bool) -> Path:
        if not isinstance(saida, str) or not saida.strip():
            raise AutomationError("ENTRADA_INVALIDA", "saida deve ser um caminho não vazio")
        try:
            destino = self.confinement.check_write(saida)
        except ConfinementError as e:
            raise AutomationError("CAMINHO_RECUSADO", str(e)) from e
        if destino == origem:
            raise AutomationError("ENTRADA_INVALIDA", "saida não pode ser o próprio arquivo de entrada")
        if destino.is_dir():
            raise AutomationError("ENTRADA_INVALIDA", f"saida é um diretório: {saida}")
        if destino.exists() and not sobrescrever:
            raise AutomationError("SAIDA_EXISTE", f"saida já existe: {saida} (use sobrescrever)")
        return destino

    @staticmethod
    def _gravar(destino: Path, texto: str, sobrescrever: bool) -> None:
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            with open(destino, "w" if sobrescrever else "x", encoding="utf-8") as f:
                f.write(texto)
        except FileExistsError as e:
            raise AutomationError("SAIDA_EXISTE", f"saida já existe: {destino} (use sobrescrever)") from e
        except OSError as e:
            raise AutomationError("ERRO_DE_ESCRITA", f"falha ao gravar {destino}: {e}") from e
