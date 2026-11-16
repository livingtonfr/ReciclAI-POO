from pathlib import Path

from app.database.conexao import conectar


def inicializar_banco(caminho):
    """Cria as tabelas previstas sem apagar registros existentes."""
    pasta = Path(__file__).parent
    arquivos = (
        "schema.sql",
        "schema_usuarios.sql",
        "schema_materiais.sql",
        "schema_eventos.sql",
        "schema_avaliacoes.sql",
        "schema_lotes.sql",
        "schema_lotes_materiais.sql",
        "schema_vinculos_lotes.sql",
    )

    with conectar(caminho) as conexao:
        for nome in arquivos:
            comando = (pasta / nome).read_text(encoding="utf-8")
            conexao.execute(comando)