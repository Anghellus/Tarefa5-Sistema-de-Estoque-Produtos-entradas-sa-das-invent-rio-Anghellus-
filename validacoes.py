"""Validações compartilhadas pela interface e pela camada de dados."""

import math


def validar_codigo(valor: str) -> str:
    codigo = str(valor).strip()
    if not codigo:
        raise ValueError("Informe o código do produto.")
    return codigo


def validar_nome(valor: str) -> str:
    nome = str(valor).strip()
    if not nome:
        raise ValueError("Informe o nome do produto.")
    return nome


def validar_categoria(valor: str) -> str:
    categoria = str(valor).strip()
    if not categoria:
        raise ValueError("Informe a categoria do produto.")
    return categoria


def validar_preco(valor: object) -> float:
    try:
        preco = float(str(valor).strip().replace(",", "."))
    except (TypeError, ValueError) as erro:
        raise ValueError("O preço deve ser um número válido.") from erro
    if not math.isfinite(preco) or preco < 0:
        raise ValueError("O preço não pode ser negativo.")
    return preco


def validar_quantidade(valor: object, campo: str = "Quantidade") -> int:
    texto = str(valor).strip()
    try:
        quantidade = int(texto)
    except (TypeError, ValueError) as erro:
        raise ValueError(campo + " deve ser um número inteiro.") from erro
    if quantidade < 0:
        raise ValueError(campo + " não pode ser negativa.")
    return quantidade


def validar_tipo(valor: str) -> str:
    tipo = str(valor).strip().lower()
    if tipo not in ("entrada", "saida"):
        raise ValueError("O tipo de movimentação deve ser entrada ou saída.")
    return tipo
