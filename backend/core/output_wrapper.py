def format_json_output(metadata: dict, content: list) -> dict:
    """
    Padroniza a saída JSON para o frontend, independentemente de qual motor 
    (LLM, Pandas, PyMuPDF, Camelot) realizou o parse.
    """
    return {
        "metadata": metadata,
        "content": content
    }
