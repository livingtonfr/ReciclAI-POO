import sqlite3

from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.model.comercial import Certificado, Transacao
from app.model.enums import StatusLote, StatusMaterial, StatusTransacao


def carregar_transacoes_do_lote(conexao, lote):
    """Reconstrói as transações já gravadas de um lote já reconstruído.

    O lote é recebido pronto, portanto não há recursão: a transação
    não recarrega o lote. O vendedor é sempre a instância do criador
    do lote. Lotes sem registros comerciais ficam como estão.
    """
    registros = conexao.execute(
        "SELECT t.*, c.id AS cert_id, c.codigo AS cert_codigo, "
        "c.data_emissao AS cert_data "
        "FROM transacoes AS t "
        "LEFT JOIN certificados AS c ON c.transacao_id = t.id "
        "WHERE t.lote_id = ? ORDER BY t.rowid",
        (str(lote.id),),
    ).fetchall()

    if not registros:
        return lote

    usuarios = UsuarioSQLiteDAO(conexao)
    compradores = {}
    transacoes = []

    for registro in registros:
        if registro["vendedor_id"] != str(lote.criador.id):
            raise ValueError(
                "O vendedor da transação difere do criador do lote."
            )

        comprador_id = registro["comprador_id"]

        if comprador_id not in compradores:
            comprador = usuarios.buscar_por_id(comprador_id)

            if comprador is None:
                raise ValueError("Comprador da transação não encontrado.")

            compradores[comprador_id] = comprador

        certificado = None

        if registro["cert_id"] is not None:
            certificado = Certificado.reconstituir(
                registro["cert_id"],
                registro["cert_codigo"],
                registro["cert_data"],
            )

        transacoes.append(
            Transacao.reconstituir(
                registro["id"],
                lote,
                lote.criador,
                compradores[comprador_id],
                registro["valor_total"],
                registro["data_transacao"],
                registro["status"],
                registro["peso_negociado"],
                certificado,
            )
        )

    lote.restaurar_transacoes(transacoes)
    return lote


class TransacaoSQLiteDAO:
    """Persiste propostas e negociações na transação recebida.

    Não executa commit. Operações compostas usam SAVEPOINT.
    """

    def __init__(self, conexao):
        self._conexao = conexao

    # ---------------------------------------------------------- consultas

    def buscar_por_id(self, transacao_id):
        from app.dao.lote_sqlite_dao import LoteSQLiteDAO

        registro = self._conexao.execute(
            "SELECT lote_id FROM transacoes WHERE id = ?",
            (str(transacao_id),),
        ).fetchone()

        if registro is None:
            return None

        lote = LoteSQLiteDAO(self._conexao).buscar_por_id(
            registro["lote_id"]
        )

        return next(
            (
                t
                for t in lote.transacoes
                if str(t.id) == str(transacao_id)
            ),
            None,
        )

    def _listar(self, coluna, usuario):
        registros = self._conexao.execute(
            f"SELECT id FROM transacoes WHERE {coluna} = ? "
            "ORDER BY rowid",
            (str(usuario.id),),
        ).fetchall()

        return [
            self.buscar_por_id(registro["id"])
            for registro in registros
        ]

    def listar_por_comprador(self, usuario):
        return self._listar("comprador_id", usuario)

    def listar_por_vendedor(self, usuario):
        return self._listar("vendedor_id", usuario)

    def buscar_por_certificado(self, certificado):
        registro = self._conexao.execute(
            "SELECT transacao_id FROM certificados WHERE id = ?",
            (str(certificado.id),),
        ).fetchone()

        if registro is None:
            return None

        return self.buscar_por_id(registro["transacao_id"])

    def listar_concluidas_por_material(self, material):
        registros = self._conexao.execute(
            "SELECT t.id FROM transacoes AS t "
            "JOIN lotes_materiais AS lm ON lm.lote_id = t.lote_id "
            "WHERE lm.material_id = ? AND t.status = 'CONCLUIDA' "
            "ORDER BY t.rowid",
            (str(material.id),),
        ).fetchall()

        return [
            self.buscar_por_id(registro["id"])
            for registro in registros
        ]

    # ------------------------------------------------------------ escrita

    def adicionar(self, transacao):
        if not isinstance(transacao, Transacao):
            raise TypeError("Transação inválida.")

        if transacao.status != StatusTransacao.PENDENTE:
            raise ValueError("Somente proposta PENDENTE pode ser incluída.")

        self._conexao.execute("SAVEPOINT adicionar_transacao")

        try:
            lote = self._conexao.execute(
                "SELECT status, criador_id FROM lotes WHERE id = ?",
                (str(transacao.lote.id),),
            ).fetchone()

            if lote is None or lote["status"] != "DISPONIVEL":
                raise ValueError(
                    "O lote deve estar persistido como DISPONIVEL."
                )

            if lote["criador_id"] != str(transacao.vendedor.id):
                raise ValueError(
                    "O vendedor persistido difere do criador do lote."
                )

            if self._conexao.execute(
                "SELECT 1 FROM transacoes WHERE id = ?",
                (str(transacao.id),),
            ).fetchone() is not None:
                raise ValueError("A transação já está cadastrada.")

            if self._conexao.execute(
                "SELECT 1 FROM transacoes WHERE lote_id = ? "
                "AND comprador_id = ? AND status = 'PENDENTE'",
                (str(transacao.lote.id), str(transacao.comprador.id)),
            ).fetchone() is not None:
                raise ValueError(
                    "Você já tem uma proposta pendente para este lote."
                )

            self._conexao.execute(
                "INSERT INTO transacoes (id, lote_id, vendedor_id, "
                "comprador_id, valor_total, data_transacao, status, "
                "peso_negociado) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)",
                (
                    str(transacao.id),
                    str(transacao.lote.id),
                    str(transacao.vendedor.id),
                    str(transacao.comprador.id),
                    transacao.valorTotal,
                    transacao.dataTransacao.isoformat(),
                    transacao.status.value,
                ),
            )

        except Exception:
            self._conexao.execute(
                "ROLLBACK TO SAVEPOINT adicionar_transacao"
            )
            raise
        finally:
            self._conexao.execute(
                "RELEASE SAVEPOINT adicionar_transacao"
            )

        return transacao

    def registrar_cancelamento(self, transacao):
        """Grava o cancelamento de uma proposta já cancelada no modelo."""
        if transacao.status != StatusTransacao.CANCELADA:
            raise ValueError("A transação não está cancelada.")

        cursor = self._conexao.execute(
            "UPDATE transacoes SET status = 'CANCELADA' "
            "WHERE id = ? AND status = 'PENDENTE'",
            (str(transacao.id),),
        )

        if cursor.rowcount != 1:
            raise ValueError("A proposta não está mais pendente.")

        return transacao

    def registrar_conclusao(self, transacao):
        """Grava, de uma só vez, o resultado de Transacao.concluir().

        Atualiza materiais (responsável, estado e eventos), remove os
        vínculos atuais do lote, marca o lote como NEGOCIADO e grava a
        transação concluída com seu peso e as concorrentes canceladas.
        Tudo dentro de um SAVEPOINT: se algo falhar, nada é mantido.
        """
        if transacao.status != StatusTransacao.CONCLUIDA:
            raise ValueError("A transação não está concluída.")

        lote = transacao.lote

        if lote.status != StatusLote.NEGOCIADO:
            raise ValueError("O lote deve estar NEGOCIADO.")

        self._conexao.execute("SAVEPOINT registrar_conclusao")

        try:
            lote_id = str(lote.id)

            registro = self._conexao.execute(
                "SELECT status FROM lotes WHERE id = ?", (lote_id,)
            ).fetchone()

            if registro is None or registro["status"] != "DISPONIVEL":
                raise ValueError(
                    "O lote persistido deve estar DISPONIVEL."
                )

            registro = self._conexao.execute(
                "SELECT status FROM transacoes WHERE id = ?",
                (str(transacao.id),),
            ).fetchone()

            if registro is None or registro["status"] != "PENDENTE":
                raise ValueError(
                    "A transação persistida deve estar PENDENTE."
                )

            composicao = {
                r["material_id"]
                for r in self._conexao.execute(
                    "SELECT material_id FROM vinculos_lotes_atuais "
                    "WHERE lote_id = ?",
                    (lote_id,),
                ).fetchall()
            }

            if composicao != {str(m.id) for m in lote.materiais}:
                raise ValueError(
                    "Os vínculos persistidos diferem do lote negociado."
                )

            for material in lote.materiais:
                if material.status not in (
                    StatusMaterial.DISPONIVEL,
                    StatusMaterial.DESTINADO,
                ):
                    raise ValueError(
                        "Estado final de material inesperado."
                    )

                self._conexao.execute(
                    "UPDATE materiais SET status = ?, "
                    "responsavel_atual_id = ? WHERE id = ?",
                    (
                        material.status.value,
                        str(material.responsavelAtual.id),
                        str(material.id),
                    ),
                )

                eventos = material.obterHistorico()

                gravados = self._conexao.execute(
                    "SELECT COUNT(*) FROM eventos_rastreio "
                    "WHERE material_id = ?",
                    (str(material.id),),
                ).fetchone()[0]

                if len(eventos) < gravados:
                    raise ValueError(
                        "O histórico persistido não pode ser reduzido."
                    )

                for ordem in range(gravados, len(eventos)):
                    evento = eventos[ordem]

                    self._conexao.execute(
                        "INSERT INTO eventos_rastreio "
                        "(id, material_id, ordem, tipo, descricao, "
                        "data_evento) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            str(evento.id),
                            str(material.id),
                            ordem,
                            evento.tipo.value,
                            evento.descricao,
                            evento.dataEvento.isoformat(),
                        ),
                    )

            self._conexao.execute(
                "DELETE FROM vinculos_lotes_atuais WHERE lote_id = ?",
                (lote_id,),
            )

            self._conexao.execute(
                "UPDATE lotes SET status = 'NEGOCIADO' WHERE id = ?",
                (lote_id,),
            )

            for item in lote.transacoes:
                self._conexao.execute(
                    "UPDATE transacoes SET status = ?, "
                    "peso_negociado = ? WHERE id = ?",
                    (
                        item.status.value,
                        item.pesoNegociado,
                        str(item.id),
                    ),
                )

        except Exception:
            self._conexao.execute(
                "ROLLBACK TO SAVEPOINT registrar_conclusao"
            )
            raise
        finally:
            self._conexao.execute(
                "RELEASE SAVEPOINT registrar_conclusao"
            )

        return transacao
