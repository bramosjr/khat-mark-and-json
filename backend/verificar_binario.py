"""Converte uma amostra de cada extensão no executável empacotado.

Uso: venv/bin/python verificar_binario.py [caminho-do-binario]
Precisa das dependências de requirements-dev.txt. As amostras são geradas na
hora, numa pasta temporária. .msg fica de fora (sem amostra).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from tests.test_formatos import AMOSTRAS, MARCA

PADRAO = Path(__file__).resolve().parent / "dist" / "markitdown-backend"


def verificar(binario: Path, pasta: Path) -> list:
    falhas = []
    for extensao, gerar in sorted(AMOSTRAS.items()):
        origem = pasta / f"amostra{extensao}"
        gerar(origem)
        for formato in ("md", "json"):
            for extra in (["--dry-run"], []):
                comando = [str(binario), "convert", str(origem), "--formato", formato, "--json", *extra]
                r = subprocess.run(comando, capture_output=True, text=True, timeout=180, cwd=pasta)
                try:
                    envelope = json.loads(r.stdout)
                except ValueError:
                    envelope = {"erro": r.stderr[-300:]}
                certo = r.returncode == 0 and (
                    envelope.get("dry_run") is True if extra
                    else MARCA in json.dumps(envelope.get("conteudo"), ensure_ascii=False))
                if not certo:
                    falhas.append(f"{extensao} {formato} {' '.join(extra)}: {str(envelope)[:200]}")
    return falhas


def main() -> int:
    binario = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PADRAO
    if not binario.is_file():
        print(f"binário não encontrado: {binario}", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory() as pasta:
        falhas = verificar(binario, Path(pasta))
    total = len(AMOSTRAS) * 4
    print(f"{total - len(falhas)} de {total} verificações ok")
    for falha in falhas:
        print("FALHA", falha)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
