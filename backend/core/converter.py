"""Núcleo de conversão (Core & Shell).

Toda a lógica de escolha de motor vive aqui. A rota HTTP (main.py), a CLI e o
servidor MCP são camadas finas que chamam estas funções. Todas as importações
pesadas (pandas, markitdown, PDF) são preguiçosas para o início ser rápido.
"""
import importlib.util
import os
import tempfile
from typing import List, Optional

PLANILHAS = ('.xlsx', '.xls', '.ods')

# Módulos que cada extensão exige além do markitdown, por formato de saída,
# no modo offline. Precisa acompanhar os caminhos de convert_file.
_DEPENDENCIAS = {
    '.docx': {"md": ("mammoth", "lxml"), "json": ("mammoth", "lxml")},
    '.pptx': {"md": ("pptx",), "json": ("pptx",)},
    '.xlsx': {"md": ("pandas", "openpyxl"), "json": ("pandas", "openpyxl")},
    '.xls': {"md": ("pandas", "xlrd"), "json": ("pandas", "xlrd")},
    '.ods': {"md": ("pandas", "odf", "openpyxl"), "json": ("pandas", "odf")},
    '.odt': {"md": ("odf",), "json": ("odf",)},
    '.csv': {"json": ("pandas",)},
    '.pdf': {"md": ("pdfminer", "pdfplumber"), "json": ("fitz", "pdfplumber")},
    '.msg': {"md": ("olefile",), "json": ("olefile",)},
}


def dependencias_ausentes(suffix: str, target_format: str) -> List[str]:
    """Módulos exigidos pela conversão que não estão instalados.

    Só localiza os módulos, sem importá-los: o dry-run continua barato.
    """
    exigidos = ("markitdown",) + _DEPENDENCIAS.get(suffix, {}).get(target_format, ())
    return [m for m in exigidos if importlib.util.find_spec(m) is None]


def _esvaziar_celulas_ausentes(markdown: str) -> str:
    """Troca por vazio as células que o pandas escreve como NaN ou NaT.

    Só mexe em células cujo conteúdo é exatamente esse, dentro de tabelas.
    """
    linhas = markdown.split("\n")
    for i, linha in enumerate(linhas):
        if linha.startswith("|"):
            linhas[i] = "|".join(
                "  " if celula in (" NaN ", " NaT ") else celula
                for celula in linha.split("|"))
    return "\n".join(linhas)


def build_markitdown(llm_provider: Optional[str] = "openai",
                     llm_api_key: Optional[str] = None,
                     llm_model: Optional[str] = None,
                     llm_base_url: Optional[str] = None):
    """Cria o MarkItDown, com client de LLM apenas quando aplicável."""
    from markitdown import MarkItDown

    provider_key = (llm_provider or "openai").strip().lower()
    # A descrição de imagens/áudio embutida no MarkItDown espera um
    # client no formato da API da OpenAI (llm_client.chat.completions...).
    # Só openai e openai_compatible falam esse formato — para os demais
    # provedores (ex.: Gemini, Anthropic), tentar usá-los aqui erraria
    # com uma chave no formato errado contra a API da OpenAI. Nesses
    # casos, a conversão de Markdown segue sem enriquecimento por LLM
    # (o provedor escolhido continua valendo para a conversão em JSON).
    if llm_api_key and llm_api_key.strip() and provider_key in ("openai", "openai_compatible"):
        from openai import OpenAI
        client_kwargs = {"api_key": llm_api_key.strip()}
        if provider_key == "openai_compatible" and llm_base_url and llm_base_url.strip():
            client_kwargs["base_url"] = llm_base_url.strip()
        return MarkItDown(llm_client=OpenAI(**client_kwargs), llm_model=llm_model)
    return MarkItDown()


def _extract_odt_text(file_path: str) -> str:
    from odf.opendocument import load
    from odf import text, teletype
    doc = load(file_path)
    extracted_text = ""
    for p in doc.getElementsByType(text.P):
        extracted_text += teletype.extractText(p) + "\n\n"
    return extracted_text.strip()


def convert_file(file_path: str, target_format: Optional[str], md,
                 llm_provider: Optional[str] = "openai",
                 llm_api_key: Optional[str] = None,
                 llm_model: Optional[str] = None,
                 llm_base_url: Optional[str] = None) -> dict:
    """Converte um arquivo local. Retorna {"markdown": ...} ou {"json_data": ...}."""
    suffix = os.path.splitext(file_path)[1].lower()

    if target_format == "json":
        if suffix in ('.xlsx', '.xls', '.csv', '.ods'):
            from core.offline_parsers import parse_tabular_to_json
            return {"json_data": parse_tabular_to_json(file_path)}
        if llm_api_key and llm_api_key.strip():
            from core.llm_parsers import parse_with_llm
            return {"json_data": parse_with_llm(
                file_path, llm_provider, llm_api_key.strip(),
                model_name=llm_model, base_url=llm_base_url,
            )}
        if suffix == '.pdf':
            from core.offline_parsers import parse_pdf_to_json_offline
            return {"json_data": parse_pdf_to_json_offline(file_path)}
        if suffix == '.odt':
            return {"json_data": {"source_type": "document", "content": _extract_odt_text(file_path)}}
        result = md.convert(file_path)
        return {"json_data": {"source_type": "document", "content": result.text_content}}

    if suffix == '.odt':
        return {"markdown": _extract_odt_text(file_path)}

    if suffix == '.ods':
        import pandas as pd
        dfs = pd.read_excel(file_path, engine="odf", sheet_name=None)
        fd, xlsx_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)
        try:
            with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
                for sheet_name, df in dfs.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            return {"markdown": _esvaziar_celulas_ausentes(md.convert(xlsx_path).text_content)}
        finally:
            try:
                os.remove(xlsx_path)
            except OSError:
                pass

    markdown = md.convert(file_path).text_content
    if suffix in PLANILHAS:
        markdown = _esvaziar_celulas_ausentes(markdown)
    return {"markdown": markdown}
