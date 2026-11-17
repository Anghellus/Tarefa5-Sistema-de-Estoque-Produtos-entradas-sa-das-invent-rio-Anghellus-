"""Ponto de entrada do Sistema de Controle de Estoque."""

from banco.conexao import inicializar_banco
from utilitarios.backup import criar_backup_automatico


def main() -> None:
    inicializar_banco()
    criar_backup_automatico()
    try:
        from interface.menu_principal import executar_interface
    except ImportError as erro:
        if erro.name == "FreeSimpleGUI":
            raise SystemExit(
                "FreeSimpleGUI não está instalado. Execute: pip install -r requirements.txt"
            ) from erro
        raise
    executar_interface()


if __name__ == "__main__":
    main()
