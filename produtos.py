"""Operações de cadastro e consulta de produtos."""

import sqlite3
from typing import List, Optional

from utilitarios.validacoes import (
    validar_categoria,
    validar_codigo,
    validar_nome,
    validar_preco,
    validar_quantidade,
)


def cadastrar_produto(
    conexao: sqlite3.Connection,
    codigo: str,
    nome: str,
    categoria: str,
    preco: object,
    estoque_minimo: object = 5,
) -> None:
    codigo_validado = validar_codigo(codigo)
    nome_validado = validar_nome(nome)
    categoria_validada = validar_categoria(categoria)
    preco_validado = validar_preco(preco)
    minimo_validado = validar_quantidade(estoque_minimo, "Estoque mínimo")

    try:
        conexao.execute(
            """INSERT INTO produtos
               (codigo, nome, categoria, preco, estoque_minimo)
               VALUES (?, ?, ?, ?, ?)""",
            (
                codigo_validado,
                nome_validado,
                categoria_validada,
                preco_validado,
                minimo_validado,
            ),
        )
        conexao.commit()
    except sqlite3.IntegrityError as erro:
        conexao.rollback()
        if "UNIQUE constraint failed" in str(erro):
            raise ValueError("Já existe um produto com esse código.") from erro
        raise ValueError("Não foi possível cadastrar o produto: " + str(erro)) from erro


def listar_produtos(
    conexao: sqlite3.Connection, categoria: Optional[str] = None
) -> List[sqlite3.Row]:
    if categoria and categoria != "Todas":
        return conexao.execute(
            """SELECT codigo, nome, categoria, preco, quantidade, estoque_minimo
               FROM produtos WHERE categoria = ? ORDER BY nome""",
            (categoria,),
        ).fetchall()
    return conexao.execute(
        """SELECT codigo, nome, categoria, preco, quantidade, estoque_minimo
           FROM produtos ORDER BY nome"""
    ).fetchall()


def listar_categorias(conexao: sqlite3.Connection) -> List[str]:
    linhas = conexao.execute(
        "SELECT DISTINCT categoria FROM produtos ORDER BY categoria"
    ).fetchall()
    return [linha["categoria"] for linha in linhas]
