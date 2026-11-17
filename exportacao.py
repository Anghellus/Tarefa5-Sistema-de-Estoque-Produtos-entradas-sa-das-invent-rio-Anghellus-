"""Exportação de relatórios de estoque para CSV."""

import csv
from pathlib import Path
from typing import Iterable, Mapping, Union


def exportar_estoque_csv(
    produtos: Iterable[Mapping[str, object]], caminho: Union[str, Path]
) -> None:
    """Salva os produtos e o valor total por item em um arquivo CSV."""
    campos = (
        "codigo",
        "nome",
        "categoria",
        "preco",
        "quantidade",
        "estoque_minimo",
        "valor_em_estoque",
        "estoque_baixo",
    )
    with Path(caminho).open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        for produto in produtos:
            linha = dict(produto)
            linha["valor_em_estoque"] = (
                float(produto["preco"]) * int(produto["quantidade"])
            )
            linha["estoque_baixo"] = (
                int(produto["quantidade"]) <= int(produto["estoque_minimo"])
            )
            escritor.writerow(linha)
