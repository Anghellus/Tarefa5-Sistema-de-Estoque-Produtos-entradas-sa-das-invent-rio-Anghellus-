"""Testes das operações centrais do sistema de estoque."""

import csv
import tempfile
import unittest
from pathlib import Path

from banco.conexao import conectar, inicializar_banco
from banco.movimentacoes import listar_movimentacoes, registrar_movimentacao
from banco.produtos import cadastrar_produto, listar_produtos
from utilitarios.autenticacao import autenticar_usuario, cadastrar_usuario
from utilitarios.backup import criar_backup_automatico
from utilitarios.exportacao import exportar_estoque_csv
from utilitarios.relatorios import calcular_indicadores


class TestSistemaEstoque(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.caminho_banco = Path(self.diretorio.name) / "teste.db"
        inicializar_banco(self.caminho_banco)
        self.conexao = conectar(self.caminho_banco)

    def tearDown(self):
        self.conexao.close()
        self.diretorio.cleanup()

    def cadastrar_exemplo(self, codigo="P001"):
        cadastrar_produto(self.conexao, codigo, "Teclado", "Periféricos", "49,90", 2)

    def test_cadastro_duplicado_e_rejeitado(self):
        self.cadastrar_exemplo()
        with self.assertRaisesRegex(ValueError, "Já existe"):
            self.cadastrar_exemplo()

    def test_movimentacoes_atualizam_saldo_e_historico(self):
        self.cadastrar_exemplo()
        registrar_movimentacao(self.conexao, "P001", "entrada", 8)
        registrar_movimentacao(self.conexao, "P001", "saida", 3)

        produto = listar_produtos(self.conexao)[0]
        self.assertEqual(produto["quantidade"], 5)
        self.assertEqual(len(listar_movimentacoes(self.conexao)), 2)

    def test_saida_acima_do_saldo_nao_altera_estoque(self):
        self.cadastrar_exemplo()
        with self.assertRaisesRegex(ValueError, "Estoque insuficiente"):
            registrar_movimentacao(self.conexao, "P001", "saida", 1)

        self.assertEqual(listar_produtos(self.conexao)[0]["quantidade"], 0)

    def test_quantidade_negativa_e_rejeitada(self):
        self.cadastrar_exemplo()
        with self.assertRaisesRegex(ValueError, "não pode ser negativa"):
            registrar_movimentacao(self.conexao, "P001", "entrada", -1)

    def test_filtro_de_categoria(self):
        self.cadastrar_exemplo()
        cadastrar_produto(self.conexao, "P002", "Caderno", "Papelaria", 12.5)

        produtos = listar_produtos(self.conexao, "Papelaria")
        self.assertEqual([produto["codigo"] for produto in produtos], ["P002"])

    def test_exportacao_csv_calcula_valor_em_estoque(self):
        self.cadastrar_exemplo()
        registrar_movimentacao(self.conexao, "P001", "entrada", 2)
        caminho_csv = Path(self.diretorio.name) / "relatorio.csv"
        exportar_estoque_csv(listar_produtos(self.conexao), caminho_csv)

        with caminho_csv.open(encoding="utf-8-sig", newline="") as arquivo:
            linha = next(csv.DictReader(arquivo))
        self.assertEqual(linha["valor_em_estoque"], "99.8")
        self.assertEqual(linha["estoque_baixo"], "True")

    def test_senhas_sao_derivadas_e_login_valida_credenciais(self):
        cadastrar_usuario(self.conexao, "Admin", "senha-segura-123")
        registro = self.conexao.execute(
            "SELECT senha_hash FROM usuarios WHERE nome_usuario = 'admin'"
        ).fetchone()

        self.assertNotEqual(registro["senha_hash"], "senha-segura-123")
        self.assertTrue(autenticar_usuario(self.conexao, "ADMIN", "senha-segura-123"))
        self.assertFalse(autenticar_usuario(self.conexao, "admin", "senha-incorreta"))

    def test_backup_preserva_o_conteudo_do_banco(self):
        self.cadastrar_exemplo()
        diretorio_backups = Path(self.diretorio.name) / "backups"
        caminho_backup = criar_backup_automatico(
            self.caminho_banco, diretorio_backups
        )
        conexao_backup = conectar(caminho_backup)
        try:
            self.assertEqual(listar_produtos(conexao_backup)[0]["codigo"], "P001")
        finally:
            conexao_backup.close()

    def test_indicadores_do_dashboard(self):
        self.cadastrar_exemplo()
        registrar_movimentacao(self.conexao, "P001", "entrada", 3)

        indicadores = calcular_indicadores(listar_produtos(self.conexao))
        self.assertEqual(indicadores, {
            "produtos": 1,
            "unidades": 3,
            "baixo_estoque": 0,
            "valor_total": 149.7,
        })


if __name__ == "__main__":
    unittest.main()
