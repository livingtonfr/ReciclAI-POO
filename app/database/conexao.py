import sqlite3
from contextlib import contextmanager
from pathlib import Path


def abrir_conexao(caminho):
    """Abre uma conexão com chaves estrangeiras e transação explícita.

    Quem chama é responsável por confirmar (commit) ou reverter
    (rollback) e por fechar a conexão.
    """
    if str(caminho) != ":memory:":
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(caminho, autocommit=True)

    try:
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA foreign_keys = ON")
        conexao.autocommit = False
    except Exception:
        conexao.close()
        raise

    return conexao


@contextmanager
def conectar(caminho):
    """Abre uma conexão e gerencia sua transação e seu fechamento."""
    conexao = abrir_conexao(caminho)

    try:
        with conexao:
            yield conexao
    finally:
        conexao.close()
