"""Descobre a codificação de um CSV. Vale para as saídas Markdown e JSON."""
import codecs
import re

# Em texto ocidental, letras acentuadas aparecem isoladas ou em grupos curtos
# ("ção"). Um arquivo de outra escrita lido como Windows-1252 gera sequências
# longas de caracteres fora do ASCII.
_SEQUENCIA_NAO_OCIDENTAL = re.compile(r"[^\x00-\x7f]{4,}")


def decodificar_csv(dados: bytes) -> str:
    """UTF-8 ou UTF-16 (com marca), depois Windows-1252, por fim detecção.

    A detecção automática fica por último porque erra em arquivos curtos em
    português: "João" em Latin-1 é lido como chinês, sem nenhum erro.
    """
    if dados.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return dados.decode("utf-16")
    try:
        return dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        texto = dados.decode("cp1252")
        if not _SEQUENCIA_NAO_OCIDENTAL.search(texto):
            return texto
    except UnicodeDecodeError:
        pass
    from charset_normalizer import from_bytes
    palpite = from_bytes(dados).best()
    if palpite is None:
        raise ValueError("não foi possível identificar a codificação do CSV")
    return str(palpite)
