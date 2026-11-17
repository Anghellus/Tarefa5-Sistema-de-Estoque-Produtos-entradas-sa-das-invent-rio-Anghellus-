"""Criação e inicialização das conexões SQLite."""

import os
import sqlite3
from pathlib import Path
from typing import Optional, Union


CAMINHO_BANCO = Path(__file__).resolve().parent.parent / "estoque.db"
CAMINHO_SCHEMA = Path(__file__).resolve().parent.parent / "banco.sql"


def conectar(caminho: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """Abre uma conexão com chaves estrangeiras habilitadas."""
    caminho_real = caminho or os.environ.get("ESTOQUE_DB_PATH") or CAMINHO_BANCO
    conexao = sqlite3.connect(str(caminho_real))
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def inicializar_banco(
    caminho: Optional[Union[str, Path]] = None,
) -> None:
    """Cria as tabelas, índices e triggers do sistema."""
    conexao = conectar(caminho)
    try:
        conexao.executescript(CAMINHO_SCHEMA.read_text(encoding="utf-8"))
    finally:
        conexao.close()
