"""Cadastro e autenticação local com senhas derivadas por PBKDF2."""

import hashlib
import hmac
import secrets
import sqlite3


ITERACOES_PBKDF2 = 600_000


def validar_usuario_senha(nome_usuario: str, senha: str) -> tuple:
    usuario = str(nome_usuario).strip().lower()
    if len(usuario) < 3:
        raise ValueError("O usuário deve ter pelo menos 3 caracteres.")
    if not usuario.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Use apenas letras, números, hífen ou sublinhado no usuário.")
    if len(senha) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")
    return usuario, senha


def cadastrar_usuario(
    conexao: sqlite3.Connection, nome_usuario: str, senha: str
) -> None:
    usuario, senha_validada = validar_usuario_senha(nome_usuario, senha)
    salt = secrets.token_bytes(16)
    senha_hash = hashlib.pbkdf2_hmac(
        "sha256", senha_validada.encode("utf-8"), salt, ITERACOES_PBKDF2
    )
    try:
        conexao.execute(
            """INSERT INTO usuarios
               (nome_usuario, senha_hash, senha_salt, iteracoes)
               VALUES (?, ?, ?, ?)""",
            (usuario, senha_hash.hex(), salt.hex(), ITERACOES_PBKDF2),
        )
        conexao.commit()
    except sqlite3.IntegrityError as erro:
        conexao.rollback()
        if "UNIQUE constraint failed" in str(erro):
            raise ValueError("Esse nome de usuário já está cadastrado.") from erro
        raise


def existe_usuario(conexao: sqlite3.Connection) -> bool:
    return conexao.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone() is not None


def autenticar_usuario(
    conexao: sqlite3.Connection, nome_usuario: str, senha: str
) -> bool:
    usuario = str(nome_usuario).strip().lower()
    registro = conexao.execute(
        """SELECT senha_hash, senha_salt, iteracoes
           FROM usuarios WHERE nome_usuario = ?""",
        (usuario,),
    ).fetchone()
    if registro is None:
        return False
    senha_calculada = hashlib.pbkdf2_hmac(
        "sha256",
        str(senha).encode("utf-8"),
        bytes.fromhex(registro["senha_salt"]),
        int(registro["iteracoes"]),
    )
    return hmac.compare_digest(senha_calculada.hex(), registro["senha_hash"])
