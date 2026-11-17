"""Backup consistente do banco SQLite com retenção dos arquivos recentes."""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from banco.conexao import CAMINHO_BANCO


def criar_backup_automatico(
    caminho_banco: Optional[Union[str, Path]] = None,
    diretorio_backup: Optional[Union[str, Path]] = None,
    manter: int = 10,
) -> Path:
    """Cria um backup SQLite e mantém apenas os backups mais recentes."""
    origem = Path(caminho_banco or os.environ.get("ESTOQUE_DB_PATH") or CAMINHO_BANCO)
    destino_dir = Path(diretorio_backup) if diretorio_backup else origem.parent / "backups"
    destino_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    destino = destino_dir / "estoque-{}.db".format(timestamp)
    temporario = destino.with_suffix(".tmp")

    try:
        origem_db = sqlite3.connect(str(origem))
        try:
            destino_db = sqlite3.connect(str(temporario))
            try:
                origem_db.backup(destino_db)
            finally:
                destino_db.close()
        finally:
            origem_db.close()
        temporario.replace(destino)
    finally:
        if temporario.exists():
            temporario.unlink()
    backups = sorted(
        destino_dir.glob("estoque-*.db"),
        key=lambda caminho: caminho.stat().st_mtime,
        reverse=True,
    )
    for backup_antigo in backups[max(1, manter):]:
        backup_antigo.unlink()
    return destino
