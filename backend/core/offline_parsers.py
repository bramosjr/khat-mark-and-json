import pandas as pd
from core.output_wrapper import format_json_output

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
            df = pd.read_csv(file_path)
            
        # Converte valores vazios/NaN para None (que viram null no JSON)
        df = df.where(pd.notnull(df), None)
            
        content = df.to_dict(orient="records")
        return format_json_output({"source_type": "tabular", "rows": len(df)}, content)
    except Exception as e:
        raise ValueError(f"Erro no parser tabular nativo: {str(e)}")

def parse_pdf_to_json_offline(file_path: str) -> dict:
    """
    Faz um processamento de PDF puro offline sem chaves de API.
    Lógica de fallback que simula o LLMSherpa usando heurística nativa (font size/weight)
    e extração de tabelas via pdfplumber/Camelot.
    """
    import fitz  # PyMuPDF
    import pdfplumber
    
    doc = fitz.open(file_path)
    content = []
    
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
            with pdfplumber.open(file_path) as pdf:
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
