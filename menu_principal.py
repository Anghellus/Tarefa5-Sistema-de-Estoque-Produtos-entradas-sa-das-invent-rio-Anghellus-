"""Interface gráfica FreeSimpleGUI do controle de estoque."""

from typing import Optional

import FreeSimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from banco.conexao import conectar
from banco.movimentacoes import listar_movimentacoes, registrar_movimentacao
from banco.produtos import cadastrar_produto, listar_categorias, listar_produtos
from utilitarios.autenticacao import (
    autenticar_usuario,
    cadastrar_usuario,
    existe_usuario,
)
from utilitarios.codigo_barras import ler_codigo_webcam
from utilitarios.exportacao import exportar_estoque_csv
from utilitarios.relatorios import calcular_indicadores


def _valores_tabela(produtos):
    return [
        [
            item["codigo"],
            item["nome"],
            item["categoria"],
            "R$ {:.2f}".format(item["preco"]),
            item["quantidade"],
            item["estoque_minimo"],
            "Baixo" if item["quantidade"] <= item["estoque_minimo"] else "OK",
        ]
        for item in produtos
    ]


def _historico_tabela(movimentacoes):
    return [
        [
            item["data"],
            item["produto_codigo"],
            item["produto_nome"],
            "Entrada" if item["tipo"] == "entrada" else "Saída",
            item["quantidade"],
        ]
        for item in movimentacoes
    ]


def _autenticar_na_interface(conexao) -> Optional[str]:
    primeiro_acesso = not existe_usuario(conexao)
    titulo = "Configuração inicial" if primeiro_acesso else "Acesso ao estoque"
    descricao = (
        "Crie o usuário administrador para este banco."
        if primeiro_acesso
        else "Entre com seu usuário e senha."
    )
    linhas = [
        [sg.Text(descricao)],
        [sg.Text("Usuário", size=(13, 1)), sg.Input(key="-USUARIO-", size=(25, 1))],
        [
            sg.Text("Senha", size=(13, 1)),
            sg.Input(key="-SENHA-", password_char="*", size=(25, 1)),
        ],
    ]
    if primeiro_acesso:
        linhas.append(
            [
                sg.Text("Confirmar senha", size=(13, 1)),
                sg.Input(key="-CONFIRMAR-SENHA-", password_char="*", size=(25, 1)),
            ]
        )
    linhas.extend(
        [
            [sg.Text("", key="-ERRO-LOGIN-", size=(45, 2), text_color="#b00020")],
            [
                sg.Button("Criar administrador" if primeiro_acesso else "Entrar", key="-ENTRAR-"),
                sg.Button("Cancelar"),
            ],
        ]
    )
    janela_login = sg.Window(titulo, linhas, modal=True, finalize=True)
    try:
        while True:
            evento, valores = janela_login.read()
            if evento in (sg.WIN_CLOSED, "Cancelar"):
                return None
            if evento != "-ENTRAR-":
                continue
            try:
                if primeiro_acesso:
                    if valores["-SENHA-"] != valores["-CONFIRMAR-SENHA-"]:
                        raise ValueError("As senhas não conferem.")
                    cadastrar_usuario(conexao, valores["-USUARIO-"], valores["-SENHA-"])
                    return str(valores["-USUARIO-"]).strip().lower()
                if autenticar_usuario(conexao, valores["-USUARIO-"], valores["-SENHA-"]):
                    return str(valores["-USUARIO-"]).strip().lower()
                janela_login["-ERRO-LOGIN-"].update("Usuário ou senha inválidos.")
            except ValueError as erro:
                janela_login["-ERRO-LOGIN-"].update(str(erro))
    finally:
        janela_login.close()


def _layout(usuario: str = ""):
    tabela_produtos = [
        ["Código", "Nome", "Categoria", "Preço", "Quantidade", "Mínimo", "Alerta"],
        [],
    ]
    tabela_movimentacoes = [
        ["Data", "Código", "Produto", "Tipo", "Quantidade"],
        [],
    ]
    coluna_cadastro = [
        [
            sg.Text("Código", size=(14, 1)),
            sg.Input(key="-CODIGO-", size=(25, 1)),
            sg.Button("Ler código (webcam)", key="-LER-CODIGO-"),
        ],
        [sg.Text("Nome", size=(14, 1)), sg.Input(key="-NOME-", size=(25, 1))],
        [sg.Text("Categoria", size=(14, 1)), sg.Input(key="-CATEGORIA-", size=(25, 1))],
        [sg.Text("Preço (R$)", size=(14, 1)), sg.Input(key="-PRECO-", size=(25, 1))],
        [
            sg.Text("Estoque mínimo", size=(14, 1)),
            sg.Input("5", key="-MINIMO-", size=(25, 1)),
        ],
        [sg.Button("Cadastrar produto", key="-CADASTRAR-")],
    ]
    coluna_movimentacao = [
        [
            sg.Text("Produto"),
            sg.Combo([], key="-PRODUTO-MOV-", size=(35, 1), readonly=True),
        ],
        [
            sg.Text("Tipo"),
            sg.Combo(
                ["entrada", "saida"],
                default_value="entrada",
                key="-TIPO-",
                readonly=True,
                size=(15, 1),
            ),
            sg.Text("Quantidade"),
            sg.Input(key="-QUANTIDADE-", size=(10, 1)),
            sg.Button("Registrar", key="-MOVIMENTAR-"),
        ],
        [
            sg.Table(
                values=[],
                headings=tabela_movimentacoes[0],
                key="-HISTORICO-",
                auto_size_columns=True,
                num_rows=12,
                expand_x=True,
                expand_y=True,
            )
        ],
    ]
    coluna_estoque = [
        [
            sg.Text("Filtrar categoria:"),
            sg.Combo(
                ["Todas"],
                default_value="Todas",
                key="-FILTRO-CATEGORIA-",
                readonly=True,
                enable_events=True,
                size=(24, 1),
            ),
            sg.Button("Atualizar", key="-ATUALIZAR-"),
        ],
        [
            sg.Table(
                values=[],
                headings=tabela_produtos[0],
                key="-TABELA-ESTOQUE-",
                auto_size_columns=True,
                num_rows=14,
                expand_x=True,
                expand_y=True,
                justification="left",
            )
        ],
    ]
    coluna_dashboard = [
        [
            sg.Frame(
                "Produtos cadastrados",
                [[sg.Text("0", key="-KPI-PRODUTOS-", font=("Any", 20, "bold"))]],
                expand_x=True,
            ),
            sg.Frame(
                "Unidades em estoque",
                [[sg.Text("0", key="-KPI-UNIDADES-", font=("Any", 20, "bold"))]],
                expand_x=True,
            ),
            sg.Frame(
                "Itens em nível baixo",
                [[sg.Text("0", key="-KPI-BAIXO-", font=("Any", 20, "bold"))]],
                expand_x=True,
            ),
            sg.Frame(
                "Valor em estoque",
                [[sg.Text("R$ 0,00", key="-KPI-VALOR-", font=("Any", 20, "bold"))]],
                expand_x=True,
            ),
        ],
        [sg.Text("Quantidade atual por produto (vermelho indica nível baixo)")],
        [sg.Canvas(key="-GRAFICO-", size=(780, 360), expand_x=True, expand_y=True)],
        [sg.Button("Atualizar painel", key="-ATUALIZAR-")],
    ]
    coluna_relatorios = [
        [
            sg.Text("Produtos com estoque baixo ou zerado:", font=("Any", 11, "bold"))
        ],
        [
            sg.Table(
                values=[],
                headings=["Produto", "Quantidade", "Estoque mínimo"],
                key="-TABELA-BAIXO-",
                auto_size_columns=True,
                num_rows=6,
                expand_x=True,
            )
        ],
        [sg.Button("Exportar relatório CSV", key="-EXPORTAR-")],
    ]
    abas = [
        sg.Tab("Dashboard", coluna_dashboard),
        sg.Tab("Produtos", coluna_cadastro),
        sg.Tab("Entradas e saídas", coluna_movimentacao),
        sg.Tab("Consulta de estoque", coluna_estoque),
        sg.Tab("Relatórios", coluna_relatorios),
    ]
    return [
        [
            sg.Text(
                "Sistema de Controle de Estoque | {}".format(usuario),
                font=("Any", 18, "bold"),
            )
        ],
        [sg.TabGroup([abas], expand_x=True, expand_y=True)],
        [sg.Text("", key="-STATUS-", size=(90, 1), text_color="#155724")],
    ]


def _desenhar_grafico(eixo, canvas, produtos) -> None:
    eixo.clear()
    itens = sorted(produtos, key=lambda item: item["quantidade"], reverse=True)[:15]
    if itens:
        nomes = [str(item["nome"])[:28] for item in reversed(itens)]
        quantidades = [int(item["quantidade"]) for item in reversed(itens)]
        cores = [
            "#dc3545" if item["quantidade"] <= item["estoque_minimo"] else "#2878b5"
            for item in reversed(itens)
        ]
        eixo.barh(nomes, quantidades, color=cores)
        eixo.set_xlabel("Unidades")
        eixo.set_title("Estoque atual por produto (até 15 maiores saldos)")
        eixo.grid(axis="x", alpha=0.2)
    else:
        eixo.text(0.5, 0.5, "Cadastre produtos para visualizar o estoque.", ha="center")
        eixo.set_axis_off()
    canvas.figure.tight_layout()
    canvas.draw_idle()


def executar_interface() -> None:
    sg.theme("LightBlue2")
    conexao = conectar()
    janela: Optional[sg.Window] = None
    try:
        usuario = _autenticar_na_interface(conexao)
        if usuario is None:
            return
        janela = sg.Window(
            "Controle de Estoque",
            _layout(usuario),
            resizable=True,
            finalize=True,
            size=(1000, 700),
        )
        figura = Figure(figsize=(8, 4), dpi=100)
        eixo_grafico = figura.add_subplot(111)
        canvas_grafico = FigureCanvasTkAgg(
            figura, master=janela["-GRAFICO-"].TKCanvas
        )
        canvas_grafico.get_tk_widget().pack(fill="both", expand=True)

        def atualizar():
            produtos = listar_produtos(conexao)
            indicadores = calcular_indicadores(produtos)
            categorias = ["Todas"] + listar_categorias(conexao)
            selecionada = janela["-FILTRO-CATEGORIA-"].get()
            janela["-FILTRO-CATEGORIA-"].update(
                values=categorias,
                value=selecionada if selecionada in categorias else "Todas",
            )
            janela["-PRODUTO-MOV-"].update(
                values=["{} - {}".format(p["codigo"], p["nome"]) for p in produtos]
            )
            filtro = janela["-FILTRO-CATEGORIA-"].get()
            filtrados = listar_produtos(conexao, filtro)
            janela["-TABELA-ESTOQUE-"].update(values=_valores_tabela(filtrados))
            janela["-HISTORICO-"].update(
                values=_historico_tabela(listar_movimentacoes(conexao))
            )
            janela["-KPI-PRODUTOS-"].update(str(indicadores["produtos"]))
            janela["-KPI-UNIDADES-"].update(str(indicadores["unidades"]))
            janela["-KPI-BAIXO-"].update(str(indicadores["baixo_estoque"]))
            janela["-KPI-VALOR-"].update(
                "R$ {:,.2f}".format(indicadores["valor_total"])
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
            baixos = [
                p for p in produtos if p["quantidade"] <= p["estoque_minimo"]
            ]
            janela["-TABELA-BAIXO-"].update(
                values=[
                    [p["nome"], p["quantidade"], p["estoque_minimo"]]
                    for p in baixos
                ]
            )
            _desenhar_grafico(eixo_grafico, canvas_grafico, produtos)

        atualizar()
        while True:
            evento, valores = janela.read()
            if evento in (sg.WIN_CLOSED, "Sair"):
                break
            try:
                if evento == "-CADASTRAR-":
                    cadastrar_produto(
                        conexao,
                        valores["-CODIGO-"],
                        valores["-NOME-"],
                        valores["-CATEGORIA-"],
                        valores["-PRECO-"],
                        valores["-MINIMO-"],
                    )
                    for chave in ("-CODIGO-", "-NOME-", "-CATEGORIA-", "-PRECO-"):
                        janela[chave].update("")
                    janela["-MINIMO-"].update("5")
                    janela["-STATUS-"].update("Produto cadastrado com sucesso!")
                    atualizar()
                elif evento == "-LER-CODIGO-":
                    codigo = ler_codigo_webcam()
                    if codigo:
                        janela["-CODIGO-"].update(codigo)
                        janela["-STATUS-"].update("Código lido da webcam.")
                elif evento == "-MOVIMENTAR-":
                    produto_selecionado = valores["-PRODUTO-MOV-"]
                    if not produto_selecionado:
                        raise ValueError("Cadastre e selecione um produto.")
                    codigo = produto_selecionado.split(" - ", 1)[0]
                    registrar_movimentacao(
                        conexao, codigo, valores["-TIPO-"], valores["-QUANTIDADE-"]
                    )
                    janela["-QUANTIDADE-"].update("")
                    janela["-STATUS-"].update("Movimentação registrada com sucesso!")
                    atualizar()
                elif evento in ("-ATUALIZAR-", "-FILTRO-CATEGORIA-"):
                    atualizar()
                elif evento == "-EXPORTAR-":
                    caminho = sg.popup_get_file(
                        "Salvar relatório de estoque",
                        save_as=True,
                        default_extension=".csv",
                        file_types=(("CSV", "*.csv"),),
                    )
                    if caminho:
                        exportar_estoque_csv(listar_produtos(conexao), caminho)
                        janela["-STATUS-"].update("Relatório CSV exportado com sucesso.")
                else:
                    continue
            except (RuntimeError, ValueError, OSError) as erro:
                janela["-STATUS-"].update(str(erro), text_color="#b00020")
            except Exception:
                janela["-STATUS-"].update(
                    "Ocorreu um erro inesperado. Consulte o terminal para detalhes.",
                    text_color="#b00020",
                )
                raise
    finally:
        if janela is not None:
            janela.close()
        conexao.close()
