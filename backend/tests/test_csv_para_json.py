"""CSV para JSON: codificações fora do UTF-8 e linhas de tamanho irregular."""
import pytest

from core.automation import Automation, AutomationError


def _converter(tmp_path, dados: bytes, **opcoes):
    origem = tmp_path / "d.csv"
    origem.write_bytes(dados)
    return Automation().executar(str(origem), formato="json", **opcoes)["conteudo"]["content"]


@pytest.mark.parametrize("codificacao", ["utf-8", "utf-8-sig", "latin-1", "cp1252", "utf-16"])
def test_texto_em_portugues_sai_certo(tmp_path, codificacao):
    texto = "nome,cidade\nJoão,São Paulo\nConceição,Maçã\n"
    assert _converter(tmp_path, texto.encode(codificacao)) == [
        {"nome": "João", "cidade": "São Paulo"}, {"nome": "Conceição", "cidade": "Maçã"}]


def test_arquivo_minimo_em_cp1252(tmp_path):
    assert _converter(tmp_path, "a,b\nJosé,1\n".encode("cp1252")) == [{"a": "José", "b": 1}]


def test_sinais_proprios_do_windows_1252(tmp_path):
    dados = "a,b\n“ótimo” – ação,preço em €\n".encode("cp1252")
    assert _converter(tmp_path, dados) == [{"a": "“ótimo” – ação", "b": "preço em €"}]


def test_japones_em_shift_jis(tmp_path):
    dados = "名前,年齢,住所\r\n佐藤太郎,30,東京\r\n三木英子,25,大阪\r\n髙橋淳,35,名古屋\r\n".encode("cp932")
    assert _converter(tmp_path, dados)[0] == {"名前": "佐藤太郎", "年齢": 30, "住所": "東京"}


def test_linha_com_coluna_a_mais_e_a_menos(tmp_path):
    dados = b'a,b\n1,"x|y"\n\n2,"l1\nl2",extra\n3\n'
    assert _converter(tmp_path, dados) == [
        {"a": 1, "b": "x|y", "Unnamed: 2": None},
        {"a": 2, "b": "l1\nl2", "Unnamed: 2": "extra"},
        {"a": 3, "b": None, "Unnamed: 2": None}]


def test_todas_as_linhas_com_coluna_a_mais_nao_perdem_dado(tmp_path):
    assert _converter(tmp_path, b"a,b\n1,2,3\n4,5,6\n") == [
        {"a": 1, "b": 2, "Unnamed: 2": 3}, {"a": 4, "b": 5, "Unnamed: 2": 6}]


def test_campo_muito_grande_em_linha_irregular(tmp_path):
    grande = "x" * 200_000
    linhas = _converter(tmp_path, f"a\n{grande},y\n".encode(), max_chars=1_000_000)
    assert linhas == [{"a": grande, "Unnamed: 1": "y"}]


def test_aspas_sem_fechar_continuam_recusadas(tmp_path):
    with pytest.raises(AutomationError) as erro:
        _converter(tmp_path, b'a,b\n1,"aberto\n2,3\n')
    assert erro.value.codigo == "CONVERSAO_FALHOU"
