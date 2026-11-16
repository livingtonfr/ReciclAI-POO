from pathlib import Path

from app.database.conexao import conectar


def inicializar_banco(caminho):
    """Cria a tabela inicial sem apagar registros existentes."""
    arquivo_sql = Path(__file__).with_name("schema.sql")
    comando = arquivo_sql.read_text(encoding="utf-8")

    with conectar(caminho) as conexao:
        conexao.execute(comando)