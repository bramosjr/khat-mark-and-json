import json

import pytest

from core.automation import Automation, AutomationError, SUPPORTED_EXTENSIONS
from core.confinement import Confinement


def _csv(tmp_path, nome="dados.csv", conteudo="a,b\n1,2\n"):
    p = tmp_path / nome
    p.write_text(conteudo, encoding="utf-8")
    return p


def test_inspecionar_descreve_o_estado_headless_offline():
    info = Automation().inspecionar()
    assert info["app"] == "khat-mark-and-json"
    assert info["modo"] == "headless"
    assert info["offline"] is True
    assert ".pdf" in info["extensoes"] and ".csv" in info["extensoes"]
    assert info["confinamento"] == {"ativo": False, "raiz_leitura": None, "raiz_escrita": None}
    assert info["limites"]["max_entrada_bytes"] > 0 and info["limites"]["max_chars"] > 0
    assert "markitdown" in info["versoes"]


def test_inspecionar_reflete_o_confinamento(tmp_path):
    info = Automation(confinement=Confinement(str(tmp_path), None)).inspecionar()
    assert info["confinamento"]["ativo"] is True
    assert info["confinamento"]["raiz_leitura"] == str(tmp_path.resolve())
    assert info["confinamento"]["raiz_escrita"] is None


def test_executar_csv_para_markdown_inline(tmp_path):
    r = Automation().executar(str(_csv(tmp_path)))
    assert r["ok"] is True and r["formato"] == "md" and r["truncado"] is False
    assert "| a | b |" in r["conteudo"]


def test_executar_csv_para_json(tmp_path):
    r = Automation().executar(str(_csv(tmp_path)), formato="json")
    assert r["conteudo"]["metadata"] == {"source_type": "tabular", "rows": 1}


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(AutomationError) as e:
        Automation().executar(str(tmp_path / "nao-existe.csv"))
    assert e.value.codigo == "ARQUIVO_NAO_ENCONTRADO"


@pytest.mark.parametrize("nome", ["a.exe", "a.zip", "semextensao"])
def test_extensao_nao_suportada(tmp_path, nome):
    p = tmp_path / nome
    p.write_bytes(b"x")
    with pytest.raises(AutomationError) as e:
        Automation().executar(str(p))
    assert e.value.codigo == "EXTENSAO_NAO_SUPORTADA"


def test_zip_nunca_e_suportado():
    assert ".zip" not in SUPPORTED_EXTENSIONS


def test_arquivo_acima_do_teto(tmp_path):
    with pytest.raises(AutomationError) as e:
        Automation(max_input_bytes=3).executar(str(_csv(tmp_path)))
    assert e.value.codigo == "ARQUIVO_GRANDE"


def test_formato_invalido(tmp_path):
    with pytest.raises(AutomationError) as e:
        Automation().executar(str(_csv(tmp_path)), formato="xml")
    assert e.value.codigo == "ENTRADA_INVALIDA"


def test_max_chars_invalido(tmp_path):
    with pytest.raises(AutomationError) as e:
        Automation().executar(str(_csv(tmp_path)), max_chars=0)
    assert e.value.codigo == "ENTRADA_INVALIDA"


def test_markdown_grande_e_truncado_com_indicacao(tmp_path):
    r = Automation().executar(str(_csv(tmp_path)), max_chars=5)
    assert r["truncado"] is True and len(r["conteudo"]) == 5


def test_json_grande_sem_saida_e_recusado(tmp_path):
    with pytest.raises(AutomationError) as e:
        Automation().executar(str(_csv(tmp_path)), formato="json", max_chars=5)
    assert e.value.codigo == "CONTEUDO_GRANDE"


def test_saida_grava_arquivo_e_nao_devolve_conteudo(tmp_path):
    destino = tmp_path / "out" / "r.md"
    r = Automation().executar(str(_csv(tmp_path)), saida=str(destino))
    assert r["saida"] == str(destino.resolve()) and "conteudo" not in r
    assert "| a | b |" in destino.read_text(encoding="utf-8")


def test_saida_json_grava_json_valido(tmp_path):
    destino = tmp_path / "r.json"
    Automation().executar(str(_csv(tmp_path)), formato="json", saida=str(destino), max_chars=5)
    assert json.loads(destino.read_text(encoding="utf-8"))["metadata"]["rows"] == 1


def test_saida_existente_exige_sobrescrever(tmp_path):
    destino = tmp_path / "r.md"
    destino.write_text("antigo")
    with pytest.raises(AutomationError) as e:
        Automation().executar(str(_csv(tmp_path)), saida=str(destino))
    assert e.value.codigo == "SAIDA_EXISTE" and destino.read_text() == "antigo"
    Automation().executar(str(_csv(tmp_path)), saida=str(destino), sobrescrever=True)
    assert destino.read_text() != "antigo"


def test_dry_run_valida_sem_converter_nem_gravar(tmp_path):
    destino = tmp_path / "r.md"
    r = Automation().executar(str(_csv(tmp_path)), saida=str(destino), dry_run=True)
    assert r["ok"] is True and r["dry_run"] is True
    assert r["saida"] == str(destino.resolve()) and not destino.exists()


def test_dry_run_tambem_recusa_o_que_o_fluxo_real_recusa(tmp_path):
    with pytest.raises(AutomationError) as e:
        Automation().executar(str(tmp_path / "x.csv"), dry_run=True)
    assert e.value.codigo == "ARQUIVO_NAO_ENCONTRADO"


def test_leitura_fora_da_raiz_vira_caminho_recusado(tmp_path):
    raiz = tmp_path / "raiz"
    raiz.mkdir()
    fora = _csv(tmp_path)
    with pytest.raises(AutomationError) as e:
        Automation(confinement=Confinement(str(raiz), str(raiz))).executar(str(fora))
    assert e.value.codigo == "CAMINHO_RECUSADO" and "outside the read root" in e.value.mensagem


def test_escrita_sem_raiz_de_escrita_vira_caminho_recusado(tmp_path):
    arq = _csv(tmp_path)
    with pytest.raises(AutomationError) as e:
        Automation(confinement=Confinement(str(tmp_path), None)).executar(
            str(arq), saida=str(tmp_path / "o.md"))
    assert e.value.codigo == "CAMINHO_RECUSADO" and "write authority is absent" in e.value.mensagem


def test_conversao_que_falha_vira_erro_de_dominio(tmp_path):
    p = tmp_path / "quebrado.xlsx"
    p.write_bytes(b"nao e xlsx")
    with pytest.raises(AutomationError) as e:
        Automation().executar(str(p), formato="json")
    assert e.value.codigo == "CONVERSAO_FALHOU"
