"""Confinamento fail-closed de leitura/escrita para a interface de automação.

Sem nenhuma raiz informada, não há confinamento. Com qualquer raiz informada,
cada direção (leitura/escrita) precisa da sua própria raiz: a ausência de uma
delas recusa o acesso naquela direção.
"""
from pathlib import Path
from typing import Optional


class ConfinementError(PermissionError):
    """Caminho recusado pelo confinamento."""


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


class Confinement:
    def __init__(self, read_root: Optional[str], write_root: Optional[str]):
        self.read_root = Path(read_root).resolve() if read_root else None
        self.write_root = Path(write_root).resolve() if write_root else None
        self.enabled = bool(self.read_root or self.write_root)

    def check_read(self, path_str: str) -> Path:
        """Resolve o caminho (seguindo symlinks) e valida contra a raiz de leitura."""
        resolved = Path(path_str).resolve()
        if not self.enabled:
            return resolved
        if self.read_root is None:
            raise ConfinementError(
                f"automation filesystem access is not granted: read authority is absent: {path_str}")
        if not _inside(resolved, self.read_root):
            raise ConfinementError(
                f"automation path rejected: outside the read root {self.read_root}: {path_str}")
        return resolved

    def check_write(self, path_str: str) -> Path:
        """Valida um caminho de escrita, mesmo que ainda não exista.

        Sobe a árvore até o primeiro ancestral existente, canonicaliza esse
        ancestral (resolvendo symlinks e `..`) e reanexa os segmentos novos.
        """
        current = Path(path_str)
        if not current.is_absolute():
            current = Path.cwd() / current
        pending = []
        while not current.exists() and current != current.parent:
            pending.append(current.name)
            current = current.parent
        resolved = current.resolve()
        for part in reversed(pending):
            if part in ("", ".", ".."):
                # `..` em segmento inexistente não é canonicalizável com segurança.
                if part == "..":
                    resolved = resolved.parent
                continue
            resolved = resolved / part
        if not self.enabled:
            return resolved
        if self.write_root is None:
            raise ConfinementError(
                f"automation filesystem access is not granted: write authority is absent: {path_str}")
        if not _inside(resolved, self.write_root):
            raise ConfinementError(
                f"automation path rejected: outside the write root {self.write_root}: {path_str}")
        return resolved
