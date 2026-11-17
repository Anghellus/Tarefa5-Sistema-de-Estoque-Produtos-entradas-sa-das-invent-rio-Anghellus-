"""Registro e histórico de entradas e saídas do estoque."""

import sqlite3
from typing import List, Optional

from utilitarios.validacoes import validar_codigo, validar_quantidade, validar_tipo


def registrar_movimentacao(
    conexao: sqlite3.Connection,
    produto_codigo: str,
    tipo: str,
    quantidade: object,
) -> None:
    codigo = validar_codigo(produto_codigo)
    tipo_validado = validar_tipo(tipo)
    quantidade_validada = validar_quantidade(quantidade)

    try:
        conexao.execute(
            """INSERT INTO movimentacoes (produto_codigo, tipo, quantidade)
               VALUES (?, ?, ?)""",
            (codigo, tipo_validado, quantidade_validada),
        )
        conexao.commit()
    except sqlite3.IntegrityError as erro:
        conexao.rollback()
        mensagem = str(erro)
        if "FOREIGN KEY constraint failed" in mensagem:
            raise ValueError("O produto informado não está cadastrado.") from erro
        if "Estoque insuficiente" in mensagem:
            raise ValueError("Estoque insuficiente para registrar esta saída.") from erro
        raise ValueError("Não foi possível registrar a movimentação: " + mensagem) from erro


def listar_movimentacoes(
    conexao: sqlite3.Connection,
    produto_codigo: Optional[str] = None,
    limite: int = 200,
) -> List[sqlite3.Row]:
    consulta = """SELECT m.id, m.tipo, m.quantidade, m.data,
                         p.codigo AS produto_codigo, p.nome AS produto_nome
                  FROM movimentacoes AS m
                  JOIN produtos AS p ON p.codigo = m.produto_codigo"""
    parametros = []
    if produto_codigo:
        consulta += " WHERE p.codigo = ?"
        parametros.append(validar_codigo(produto_codigo))
    consulta += " ORDER BY m.data DESC, m.id DESC LIMIT ?"
    parametros.append(max(1, int(limite)))
    return conexao.execute(consulta, parametros).fetchall()
