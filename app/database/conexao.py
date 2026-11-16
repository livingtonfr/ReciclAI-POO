import sqlite3
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def conectar(caminho):
    """Abre uma conexão e gerencia sua transação e seu fechamento."""
    if str(caminho) != ":memory:":
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(caminho, autocommit=True)

    try:
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA foreign_keys = ON")
        conexao.autocommit = False

        with conexao:
            yield conexao
    finally:
        conexao.close()