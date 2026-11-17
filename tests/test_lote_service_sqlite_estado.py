import sqlite3
import unittest

from tests import test_lote_service_sqlite_composicao as base

from app.dao.lote_sqlite_dao import LoteSQLiteDAO
from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.database.conexao import conectar
from app.model.enums import StatusLote, StatusMaterial
from app.services.lote_service import AcessoLoteNegadoError


class TestLoteServiceSQLiteEstado(unittest.TestCase):
    setUp = base.TestLoteServiceSQLiteComposicao.setUp
    servico = base.TestLoteServiceSQLiteComposicao.servico
    criar = base.TestLoteServiceSQLiteComposicao.criar

    def test_pesagem_e_disponibilizacao_persistem(self):
        lote = self.criar()

        with conectar(self.caminho) as conexao:
            servico = self.servico(conexao)

            pesado = servico.registrar_pesagem(
                lote.id,
                self.usuario,
                9.5,
            )

            self.assertEqual(pesado.pesoRegistrado, 9.5)

        with conectar(self.caminho) as conexao:
            servico = self.servico(conexao)

            recuperado = servico.buscar_do_usuario(
                lote.id,
                self.usuario,
            )

            self.assertEqual(recuperado.pesoRegistrado, 9.5)

            disponivel = servico.disponibilizar(
                lote.id,
                self.usuario,
            )

            self.assertIs(
                disponivel.status,
                StatusLote.DISPONIVEL,
            )

        with conectar(self.caminho) as conexao:
            recuperado = LoteSQLiteDAO(conexao).buscar_por_id(
                lote.id
            )

            self.assertIs(
                recuperado.status,
                StatusLote.DISPONIVEL,
            )
            self.assertEqual(recuperado.pesoRegistrado, 9.5)
            self.assertIs(
                recuperado.materiais[0].loteAtual,
                recuperado,
            )

    def test_cancelamento_preserva_composicao_e_pesagem(self):
        lote = self.criar()

        with conectar(self.caminho) as conexao:
            servico = self.servico(conexao)

            servico.registrar_pesagem(
                lote.id,
                self.usuario,
                9.5,
            )
            servico.disponibilizar(lote.id, self.usuario)

            cancelado = servico.cancelar(
                lote.id,
                self.usuario,
            )

            self.assertIs(
                cancelado.status,
                StatusLote.CANCELADO,
            )
            self.assertIsNone(
                cancelado.materiais[0].loteAtual
            )

        with conectar(self.caminho) as conexao:
            recuperado = LoteSQLiteDAO(conexao).buscar_por_id(
                lote.id
            )
            material = MaterialSQLiteDAO(conexao).buscar_por_id(
                self.materiais[0].id
            )

            self.assertIs(
                recuperado.status,
                StatusLote.CANCELADO,
            )
            self.assertEqual(recuperado.pesoRegistrado, 9.5)
            self.assertEqual(
                [m.id for m in recuperado.materiais],
                [self.materiais[0].id],
            )
            self.assertIs(
                material.status,
                StatusMaterial.DISPONIVEL,
            )
            self.assertIsNone(material.loteAtual)
            self.assertEqual(len(material.obterHistorico()), 2)

    def test_recusas_preservam_estado_persistido(self):
        lote = self.criar()

        with conectar(self.caminho) as conexao:
            servico = self.servico(conexao)

            servico.registrar_pesagem(
                lote.id,
                self.usuario,
                9.5,
            )

            antes = conexao.total_changes

            with self.assertRaises(ValueError):
                servico.registrar_pesagem(
                    lote.id,
                    self.usuario,
                    50_001,
                )

            with self.assertRaises(AcessoLoteNegadoError):
                servico.registrar_pesagem(
                    lote.id,
                    self.outro,
                    8,
                )

            with self.assertRaises(AcessoLoteNegadoError):
                servico.disponibilizar(lote.id, self.outro)

            with self.assertRaises(AcessoLoteNegadoError):
                servico.cancelar(lote.id, self.outro)

            self.assertEqual(conexao.total_changes, antes)

        with conectar(self.caminho) as conexao:
            servico = self.servico(conexao)
            recuperado = servico.buscar_do_usuario(
                lote.id,
                self.usuario,
            )

            self.assertEqual(recuperado.pesoRegistrado, 9.5)
            self.assertIs(
                recuperado.status,
                StatusLote.EM_FORMACAO,
            )

            servico.cancelar(lote.id, self.usuario)
            antes = conexao.total_changes

            with self.assertRaises(ValueError):
                servico.registrar_pesagem(
                    lote.id,
                    self.usuario,
                    8,
                )

            with self.assertRaises(ValueError):
                servico.disponibilizar(lote.id, self.usuario)

            with self.assertRaises(ValueError):
                servico.cancelar(lote.id, self.usuario)

            self.assertEqual(conexao.total_changes, antes)

    def test_falhas_sql_preservam_lote_e_vinculos(self):
        lote = self.criar()

        with conectar(self.caminho) as conexao:
            conexao.execute(
                "CREATE TEMP TRIGGER falhar_estado "
                "BEFORE UPDATE ON lotes "
                "BEGIN "
                "SELECT RAISE(ABORT, 'Falha simulada'); "
                "END"
            )

            servico = self.servico(conexao)

            operacoes = (
                lambda: servico.registrar_pesagem(
                    lote.id, self.usuario, 9.5
                ),
                lambda: servico.disponibilizar(
                    lote.id, self.usuario
                ),
                lambda: servico.cancelar(
                    lote.id, self.usuario
                ),
            )

            for indice, operacao in enumerate(operacoes):
                with self.subTest(operacao=indice):
                    with self.assertRaises(sqlite3.IntegrityError):
                        operacao()

                    recuperado = LoteSQLiteDAO(
                        conexao
                    ).buscar_por_id(lote.id)

                    self.assertIs(
                        recuperado.status,
                        StatusLote.EM_FORMACAO,
                    )
                    self.assertIsNone(recuperado.pesoRegistrado)
                    self.assertIs(
                        recuperado.materiais[0].status,
                        StatusMaterial.EM_LOTE,
                    )
                    self.assertIs(
                        recuperado.materiais[0].loteAtual,
                        recuperado,
                    )

    def test_rollback_externo_reverte_as_tres_operacoes(self):
        lote = self.criar()

        with self.assertRaises(RuntimeError):
            with conectar(self.caminho) as conexao:
                servico = self.servico(conexao)

                servico.registrar_pesagem(
                    lote.id,
                    self.usuario,
                    9.5,
                )
                servico.disponibilizar(
                    lote.id,
                    self.usuario,
                )
                servico.cancelar(
                    lote.id,
                    self.usuario,
                )

                raise RuntimeError("Falha posterior")

        with conectar(self.caminho) as conexao:
            recuperado = LoteSQLiteDAO(conexao).buscar_por_id(
                lote.id
            )

            self.assertIs(
                recuperado.status,
                StatusLote.EM_FORMACAO,
            )
            self.assertIsNone(recuperado.pesoRegistrado)
            self.assertIs(
                recuperado.materiais[0].status,
                StatusMaterial.EM_LOTE,
            )
            self.assertIs(
                recuperado.materiais[0].loteAtual,
                recuperado,
            )


if __name__ == "__main__":
    unittest.main()