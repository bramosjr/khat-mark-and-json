"""Gera a lista de componentes de terceiros e suas licenças, para os pacotes.

Cobre as dependências de execução do backend (a partir de requirements.txt),
o inicializador do PyInstaller e as bibliotecas da interface (a partir de
frontend/package.json). Dependências de desenvolvimento ficam de fora.

Todo componente precisa sair com texto. Quando a distribuição instalada não
traz nenhum, ele vem de licenses/terceiros/<nome>-<versão>.txt, obtido da
fonte oficial daquela versão. Sem um nem outro, a geração falha: ao atualizar
uma dessas bibliotecas, o texto precisa ser conferido de novo.
"""
import json
import re
import sys
import sysconfig
from importlib.metadata import distribution
from pathlib import Path

from packaging.requirements import Requirement

BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
SAIDA = BACKEND_DIR / "dist" / "LICENCAS-TERCEIROS.txt"
TEXTOS_EXTERNOS = BACKEND_DIR.parent / "licenses" / "terceiros"
_SEPARADOR = "=" * 70
_ARQUIVO_DE_LICENCA = re.compile(r"(licen[sc]e|copying|notice)", re.IGNORECASE)


class LicencaAusente(RuntimeError):
    pass


def _e_texto_de_licenca(arquivo) -> bool:
    if arquivo.suffix in (".py", ".pyc"):
        return False
    # tudo o que está na pasta "licenses" dos metadados é texto de licença,
    # mesmo com nomes como "pdfium.txt" ou "Apache-2.0.txt"
    pastas = arquivo.parts[:-1]
    na_pasta = any(p.endswith(".dist-info") for p in pastas) and any(
        p.lower() == "licenses" for p in pastas)
    return na_pasta or bool(_ARQUIVO_DE_LICENCA.search(arquivo.name))


def _dependencias_python(requisitos: Path) -> list:
    """Fecho das dependências instaladas, respeitando extras e marcadores."""
    fila = [Requirement(linha) for linha in requisitos.read_text(encoding="utf-8").splitlines()
            if linha.strip() and not linha.startswith(("#", "-"))]
    vistos = {}
    while fila:
        pedido = fila.pop()
        chave = re.sub(r"[-_.]+", "-", pedido.name).lower()
        anteriores = vistos.get(chave, (None, None))[1]
        if anteriores is not None and pedido.extras <= anteriores:
            continue
        dist = distribution(pedido.name)  # ausente aqui é erro de build
        extras = set(pedido.extras) | (anteriores or set())
        vistos[chave] = (dist, extras)
        for texto in dist.requires or []:
            requisito = Requirement(texto)
            if requisito.marker is None or any(
                    requisito.marker.evaluate({"extra": e}) for e in (extras or {""})):
                fila.append(requisito)
    return [vistos[c][0] for c in sorted(vistos)]


def _licenca_declarada(meta) -> str:
    classificadores = [c.split("::")[-1].strip() for c in meta.get_all("Classifier", [])
                       if c.startswith("License")]
    primeira_linha = (meta.get("License") or "").strip().split("\n")[0]
    return (meta.get("License-Expression") or "; ".join(classificadores)
            or primeira_linha or "não declarada")


def _secao_python(dist, nome=None) -> str:
    meta = dist.metadata
    partes = [f"## {nome or meta['Name']} {dist.version}",
              f"Licença declarada: {_licenca_declarada(meta)}",
              f"Origem: https://pypi.org/project/{meta['Name']}/{dist.version}/"]
    textos = sorted((f for f in dist.files or [] if _e_texto_de_licenca(f)), key=str)
    for arquivo in textos:
        partes.append(f"--- {arquivo.name} ---\n"
                      + arquivo.locate().read_text(encoding="utf-8", errors="replace").strip())
    if not textos:
        chave = re.sub(r"[-_.]+", "-", meta["Name"]).lower()
        externo = TEXTOS_EXTERNOS / f"{chave}-{dist.version}.txt"
        if not externo.is_file():
            raise LicencaAusente(f"sem texto de licença para {chave} {dist.version}: "
                                 f"obtenha-o da fonte oficial e salve em {externo}")
        partes.append(externo.read_text(encoding="utf-8").strip())
    return "\n".join(partes)


def _secao_do_interpretador() -> str:
    candidatos = (Path(sysconfig.get_path("stdlib")) / "LICENSE.txt",
                  Path(sys.base_prefix) / "LICENSE.txt")  # Linux; Windows
    arquivo = next((c for c in candidatos if c.is_file()), None)
    if arquivo is None:
        raise LicencaAusente("licença do Python não encontrada: "
                             + ", ".join(map(str, candidatos)))
    return (f"## Python {sys.version.split()[0]}\nLicença declarada: PSF-2.0\n"
            "Origem: https://docs.python.org/3/license.html\n--- LICENSE.txt ---\n"
            + arquivo.read_text(encoding="utf-8", errors="replace").strip())


def _secoes_interface() -> list:
    def ler(pasta):
        return json.loads((pasta / "package.json").read_text(encoding="utf-8"))

    fila, vistos = list(ler(FRONTEND_DIR)["dependencies"]), {}
    while fila:
        nome = fila.pop()
        if nome not in vistos:
            pasta = FRONTEND_DIR / "node_modules" / nome
            vistos[nome] = (pasta, ler(pasta))
            fila.extend(vistos[nome][1].get("dependencies", {}))
    secoes = []
    for nome, (pasta, pacote) in sorted(vistos.items()):
        partes = [f"## {nome} {pacote['version']}",
                  f"Licença declarada: {pacote.get('license', 'não declarada')}",
                  f"Origem: https://www.npmjs.com/package/{nome}/v/{pacote['version']}"]
        textos = [f"--- {a.name} ---\n" + a.read_text(encoding="utf-8", errors="replace").strip()
                  for a in sorted(pasta.iterdir())
                  if a.is_file() and _ARQUIVO_DE_LICENCA.search(a.name)]
        if not textos:
            raise LicencaAusente(f"sem texto de licença para {nome} {pacote['version']}")
        partes += textos
        secoes.append("\n".join(partes))
    return secoes


def gerar(saida: Path = SAIDA) -> None:
    secoes = [_secao_python(d) for d in _dependencias_python(BACKEND_DIR / "requirements.txt")]
    # o inicializador do PyInstaller vai dentro do executável
    secoes.append(_secao_python(distribution("pyinstaller"), "PyInstaller"))
    secoes.append(_secao_do_interpretador())
    secoes += _secoes_interface()
    cabecalho = ("Componentes de terceiros do Khat Mark And Json\n"
                 "Cada um mantém a própria licença. Ver também NOTICE.md.\n")
    saida.parent.mkdir(parents=True, exist_ok=True)
    corpo = "\n\n".join(f"{_SEPARADOR}\n{secao}" for secao in secoes)
    saida.write_text(cabecalho + "\n" + corpo + "\n", encoding="utf-8")


if __name__ == "__main__":
    gerar()
    print(f"licenças de terceiros geradas em {SAIDA}")
