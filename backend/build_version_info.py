"""Gera backend/dist/version-info.json com a versão do markitdown e do app
embutidas no build, para exibição na tela "Sobre" e checagem de atualização."""
import json
import sys
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_PACKAGE_JSON = BACKEND_DIR.parent / "frontend" / "package.json"
OUTPUT_PATH = BACKEND_DIR / "dist" / "version-info.json"


def read_app_version(package_json_path: Path) -> str:
    with open(package_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["version"]


def generate_version_info(markitdown_version: str, app_version: str, built_at: str = None) -> dict:
    return {
        "app_version": app_version,
        "markitdown_version": markitdown_version,
        "built_at": built_at or datetime.now(timezone.utc).isoformat(),
    }


def write_version_info(info: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
        f.write("\n")


def main() -> None:
    try:
        markitdown_version = version("markitdown")
    except PackageNotFoundError:
        print("ERRO: pacote 'markitdown' não encontrado no ambiente ativo.", file=sys.stderr)
        sys.exit(1)

    app_version = read_app_version(FRONTEND_PACKAGE_JSON)
    info = generate_version_info(markitdown_version, app_version)
    write_version_info(info, OUTPUT_PATH)
    print(f"version-info.json gerado em {OUTPUT_PATH}: {info}")


if __name__ == "__main__":
    main()
