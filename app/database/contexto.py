"""Ligação entre o Flask e o SQLite.

Política de transação (uma conexão por requisição):
- a conexão é aberta sob demanda, na primeira vez que é usada;
- ao final da requisição, se a resposta for de sucesso ou redirecionamento
  (status < 400), a transação é confirmada; caso contrário, revertida;
- se uma exceção não tratada escapar da rota, a transação é revertida;
- a conexão é sempre fechada ao final.

Operações compostas (lotes, propostas, conclusão, certificado) usam
SAVEPOINT nos DAOs, portanto uma falha de negócio tratada pelo
controller (flash + redirect) não deixa gravação parcial.
"""

import threading
from pathlib import Path

from flask import current_app, g

from app.database.conexao import abrir_conexao, conectar
from app.database.inicializacao import inicializar_banco
from app.database.seed import semear_demo

_bloqueio = threading.Lock()
_preparados = set()


def preparar_banco(caminho):
    """Cria o banco e a carga inicial, uma vez por processo e caminho."""
    chave = str(caminho)

    with _bloqueio:
        if chave in _preparados and Path(caminho).exists():
            return

        inicializar_banco(caminho)

        with conectar(caminho) as conexao:
            semear_demo(conexao)

        _preparados.add(chave)


def obter_conexao():
    if "conexao_db" not in g:
        caminho = current_app.config["DATABASE_PATH"]
        preparar_banco(caminho)
        g.conexao_db = abrir_conexao(caminho)

    return g.conexao_db


def _confirmar_ou_reverter(resposta):
    conexao = g.get("conexao_db")

    if conexao is not None:
        if resposta.status_code < 400:
            conexao.commit()
        else:
            conexao.rollback()

    return resposta


def _fechar_conexao(erro=None):
    conexao = g.pop("conexao_db", None)

    if conexao is not None:
        try:
            conexao.rollback()
        finally:
            conexao.close()


def registrar(app):
    app.after_request(_confirmar_ou_reverter)
    app.teardown_appcontext(_fechar_conexao)

    @app.context_processor
    def _contexto_reset():
        return {
            "reset_demo_habilitado": bool(
                app.config.get("PERMITIR_RESET_DEMO")
            ) and app.debug
        }
