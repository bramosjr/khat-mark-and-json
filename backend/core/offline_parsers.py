import csv
import io
import json
import pandas as pd
from core.codificacao_csv import decodificar_csv
from core.output_wrapper import format_json_output

def _igualar_colunas(texto: str) -> str:
    """Se alguma linha passa do cabeçalho, completa todas até a mais larga.

    Sem isso o pandas falha ou, quando todas as linhas de dados têm um campo a
    mais, usa a primeira coluna como índice e ela some da saída. Arquivos sem
    esse problema voltam sem nenhuma alteração.
    """
    limite_anterior = csv.field_size_limit()
    csv.field_size_limit(max(limite_anterior, len(texto) + 1))
    try:
        def linhas(estrito):
            leitor = csv.reader(io.StringIO(texto, newline=""), strict=estrito)
            return [l for l in leitor if l and not (len(l) == 1 and not l[0].strip())]

        encontradas = linhas(False)
        if not encontradas:
            return texto
        largura = max(map(len, encontradas))
        if largura == len(encontradas[0]):
            return texto
        cabecalho, *registros = linhas(True)  # aspas inválidas não são adivinhadas
    finally:
        csv.field_size_limit(limite_anterior)

    cabecalho += [f"Unnamed: {i}" for i in range(len(cabecalho), largura)]
    saida = io.StringIO(newline="")
    escritor = csv.writer(saida)
    escritor.writerow(cabecalho)
    escritor.writerows(l + [""] * (largura - len(l)) for l in registros)
    return saida.getvalue()


def _ler_csv(file_path: str) -> pd.DataFrame:
    with open(file_path, "rb") as arquivo:
        texto = decodificar_csv(arquivo.read())
    return pd.read_csv(io.StringIO(_igualar_colunas(texto), newline=""))

def parse_tabular_to_json(file_path: str) -> dict:
    """
    Usa o Pandas nativo para ler arquivos tabulares de forma muito mais eficiente e
    limpa que um LLM faria. Evita alucinações de modelos.
    """
    try:
        if file_path.lower().endswith('.xlsx') or file_path.lower().endswith('.xls'):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.ods'):
            df = pd.read_excel(file_path, engine='odf')
        else:
            # Assume CSV as fallback for tabular
            df = _ler_csv(file_path)
            
        # Converte para JSON e volta via df.to_json(), não df.to_dict(): em
        # colunas numéricas, .where(pd.notnull(df), None) não remove o NaN
        # de fato (o dtype float64 permanece e o None atribuído volta a virar
        # NaN) — json.dumps rejeita NaN ("Out of range float values are not
        # JSON compliant"), o que derrubava a resposta a meio da
        # serialização (o cliente via "Failed to fetch", não um erro
        # tratado). df.to_json() converte NaN para null corretamente,
        # independente do dtype da coluna.
        content = json.loads(df.to_json(orient="records", date_format="iso"))
        return format_json_output({"source_type": "tabular", "rows": len(df)}, content)
    except Exception as e:
        raise ValueError(f"Erro no parser tabular nativo: {str(e)}")

def parse_pdf_to_json_offline(file_path: str) -> dict:
    """
    Faz um processamento de PDF puro offline sem chaves de API.
    Lógica de fallback que simula o LLMSherpa usando heurística nativa (font size/weight)
    e extração de tabelas via pdfplumber.
    """
    import fitz  # PyMuPDF
    import pdfplumber

    content = []

    # fitz.open() e pdfplumber.open() abrem o arquivo inteiro na memória —
    # abrir cada um só uma vez (fora do loop de páginas) e fechar sempre no
    # finally, mesmo se algo no meio falhar. Antes, o pdfplumber era reaberto
    # (relendo o PDF inteiro) uma vez POR PÁGINA, e nenhum dos dois arquivos
    # era fechado ao final — o que também podia deixar o arquivo temporário
    # travado (principalmente no Windows) até o processo inteiro terminar.
    doc = fitz.open(file_path)
    try:
        with pdfplumber.open(file_path) as pdf:
            # Heurística simplificada de Blocos
            for page_num, page in enumerate(doc):
                # 1. Extração de blocos de texto nativos
                blocks = page.get_text("blocks")
                for block in blocks:
                    text = block[4].strip()
                    if text:
                        content.append({
                            "type": "text",
                            "page": page_num + 1,
                            "content": text
                        })

                # 2. Extração de tabelas (pdfplumber)
                try:
                    plumber_page = pdf.pages[page_num]
                    tables = plumber_page.extract_tables()
                    for table in tables:
                        if table:
                            content.append({
                                "type": "table",
                                "page": page_num + 1,
                                "content": table
                            })
                except Exception:
                    pass  # Se falhar em ler tabelas da página, segue adiante

        return format_json_output({"source_type": "pdf_offline_heuristic", "pages": len(doc)}, content)
    finally:
        doc.close()
