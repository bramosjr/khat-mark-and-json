import os

import pytest

from core.confinement import Confinement, ConfinementError


def test_sem_raizes_nao_confina(tmp_path):
    c = Confinement(None, None)
    assert c.enabled is False
    assert c.check_read(str(tmp_path / "x")) == (tmp_path / "x").resolve()
    assert c.check_write(str(tmp_path / "y")) == (tmp_path / "y").resolve()


def test_leitura_dentro_da_raiz_ok(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    c = Confinement(str(tmp_path), None)
    assert c.check_read(str(tmp_path / "a.txt")) == (tmp_path / "a.txt").resolve()


def test_leitura_fora_da_raiz_recusada(tmp_path):
    raiz = tmp_path / "raiz"
    raiz.mkdir()
    fora = tmp_path / "fora.txt"
    fora.write_text("x")
    with pytest.raises(ConfinementError, match="outside the read root"):
        Confinement(str(raiz), None).check_read(str(fora))


def test_leitura_sem_raiz_de_leitura_quando_so_ha_raiz_de_escrita(tmp_path):
    with pytest.raises(ConfinementError, match="read authority is absent"):
        Confinement(None, str(tmp_path)).check_read(str(tmp_path / "a.txt"))


def test_escrita_sem_raiz_de_escrita_quando_so_ha_raiz_de_leitura(tmp_path):
    with pytest.raises(ConfinementError, match="write authority is absent"):
        Confinement(str(tmp_path), None).check_write(str(tmp_path / "a.txt"))


def test_traversal_com_pontos_pontos_recusado(tmp_path):
    raiz = tmp_path / "raiz"
    raiz.mkdir()
    (tmp_path / "segredo.txt").write_text("x")
    c = Confinement(str(raiz), str(raiz))
    with pytest.raises(ConfinementError):
        c.check_read(str(raiz / ".." / "segredo.txt"))
    with pytest.raises(ConfinementError):
        c.check_write(str(raiz / ".." / "novo.txt"))


def test_symlink_que_escapa_da_raiz_recusado(tmp_path):
    raiz = tmp_path / "raiz"
    raiz.mkdir()
    alvo = tmp_path / "segredo.txt"
    alvo.write_text("x")
    link = raiz / "atalho.txt"
    os.symlink(alvo, link)
    with pytest.raises(ConfinementError, match="outside the read root"):
        Confinement(str(raiz), None).check_read(str(link))


def test_escrita_de_arquivo_novo_em_subpasta_inexistente_dentro_da_raiz(tmp_path):
    c = Confinement(None, str(tmp_path))
    destino = tmp_path / "novo" / "sub" / "out.md"
    assert c.check_write(str(destino)) == destino.resolve()


def test_escrita_nova_fora_da_raiz_recusada(tmp_path):
    raiz = tmp_path / "raiz"
    raiz.mkdir()
    with pytest.raises(ConfinementError, match="outside the write root"):
        Confinement(None, str(raiz)).check_write(str(tmp_path / "outro" / "out.md"))
