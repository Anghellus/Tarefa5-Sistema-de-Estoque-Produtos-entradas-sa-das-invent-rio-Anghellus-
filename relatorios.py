"""Cálculo dos indicadores do painel de estoque."""

from typing import Iterable, Mapping


def calcular_indicadores(produtos: Iterable[Mapping[str, object]]) -> dict:
    itens = list(produtos)
    return {
        "produtos": len(itens),
        "unidades": sum(int(item["quantidade"]) for item in itens),
        "baixo_estoque": sum(
            int(item["quantidade"]) <= int(item["estoque_minimo"]) for item in itens
        ),
        "valor_total": sum(
            float(item["preco"]) * int(item["quantidade"]) for item in itens
        ),
    }
