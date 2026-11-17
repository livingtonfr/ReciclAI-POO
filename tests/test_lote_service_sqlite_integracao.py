import unittest
from unittest.mock import Mock

from tests import test_lote_service_sqlite_composicao as base

from app.dao.lote_sqlite_dao import LoteSQLiteDAO
from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.database.conexao import conectar
from app.model.enums import StatusLote
from app.model.servicos_ia import PrecificacaoIA
from app.services.lote_service import (
    AcessoLoteNegadoError,
    LoteService,
)


class TestLoteServiceSQLiteIntegracao(unittest.TestCase):
    setUp = base.TestLoteServiceSQLiteComposicao.setUp
    servico = base.TestLoteServiceSQLiteComposicao.servico
    criar = base.TestLoteServiceSQLiteComposicao.criar

    def servico_com_cotacao(self, conexao):
        return LoteService(
            LoteSQLiteDAO(conexao),
            MaterialSQLiteDAO(conexao),
            servico_precificacao=PrecificacaoIA(2.75),
        )

    def test_cota_lote_reconstruido_sem_gravar(self):
        lote = self.criar()

        with conectar(self.caminho) as conexao:
            servico = self.servico_com_cotacao(conexao)
            antes = conexao.total_changes

            cotacao = servico.cotar(
                lote.id,
                self.usuario,
                15,
            )

            self.assertEqual(conexao.total_changes, antes)
            self.assertEqual(cotacao.lote.id, lote.id)
            self.assertIsNone(cotacao.material)
            self.assertEqual(cotacao.valorPorKg, 2.75)
            self.assertEqual(cotacao.horizonteDias, 15)

            self.assertIsNot(
                cotacao.lote.criador,
                self.usuario,
            )
            self.assertEqual(
                cotacao.lote.criador.id,
                self.usuario.id,
            )
            self.assertIs(
                cotacao.lote.materiais[0].responsavelAtual,
                cotacao.lote.criador,
            )
            self.assertIs(
                cotacao.lote.materiais[0].loteAtual,
                cotacao.lote,
            )

    def test_outro_usuario_nao_aciona_precificacao(self):
        lote = self.criar()
        precificacao = Mock()

        with conectar(self.caminho) as conexao:
            servico = LoteService(
                LoteSQLiteDAO(conexao),
                MaterialSQLiteDAO(conexao),
                servico_precificacao=precificacao,
            )

            antes = conexao.total_changes

            with self.assertRaises(AcessoLoteNegadoError):
                servico.cotar(
                    lote.id,
                    self.outro,
                    15,
                )

            precificacao.cotarLote.assert_not_called()
            self.assertEqual(conexao.total_changes, antes)

    def test_prazo_invalido_e_servico_nao_configurado(self):
        lote = self.criar()

        with conectar(self.caminho) as conexao:
            antes = conexao.total_changes

            with self.assertRaises(RuntimeError):
                self.servico(conexao).cotar(
                    lote.id,
                    self.usuario,
                    15,
                )

            with self.assertRaises(ValueError):
                self.servico_com_cotacao(conexao).cotar(
                    lote.id,
                    self.usuario,
                    0,
                )

            self.assertEqual(conexao.total_changes, antes)

    def test_fluxo_integrado_e_reagrupamento(self):
        lote = self.criar()

        # Inclusão e pesagem pelo serviço.
        with conectar(self.caminho) as conexao:
            servico = self.servico_com_cotacao(conexao)

            servico.adicionar_material(
                lote.id,
                self.materiais[1].id,
                self.usuario,
            )
            servico.registrar_pesagem(
                lote.id,
                self.usuario,
                29,
            )

        # Reabre, confere e remove o segundo material.
        with conectar(self.caminho) as conexao:
            servico = self.servico_com_cotacao(conexao)

            recuperado = servico.buscar_do_usuario(
                lote.id,
                self.usuario,
            )

            self.assertEqual(
                recuperado.calcularPesoTotal(),
                30,
            )
            self.assertEqual(recuperado.pesoRegistrado, 29)

            alterado = servico.remover_material(
                lote.id,
                self.materiais[1].id,
                self.usuario,
            )

            self.assertIsNone(alterado.pesoRegistrado)

        # Reabre, registra nova pesagem e disponibiliza.
        with conectar(self.caminho) as conexao:
            servico = self.servico_com_cotacao(conexao)

            recuperado = servico.buscar_do_usuario(
                lote.id,
                self.usuario,
            )

            self.assertIsNone(recuperado.pesoRegistrado)
            self.assertEqual(
                [m.id for m in recuperado.materiais],
                [self.materiais[0].id],
            )

            servico.registrar_pesagem(
                lote.id,
                self.usuario,
                9.5,
            )
            servico.disponibilizar(
                lote.id,
                self.usuario,
            )

        # Reabre, cota e cancela.
        with conectar(self.caminho) as conexao:
            servico = self.servico_com_cotacao(conexao)

            cotacao = servico.cotar(
                lote.id,
                self.usuario,
                15,
            )

            self.assertIs(
                cotacao.lote.status,
                StatusLote.DISPONIVEL,
            )
            self.assertEqual(
                cotacao.lote.pesoRegistrado,
                9.5,
            )

            servico.cancelar(lote.id, self.usuario)

        # Os materiais liberados podem formar outro lote.
        with conectar(self.caminho) as conexao:
            servico = self.servico_com_cotacao(conexao)

            disponiveis = servico.listar_materiais_disponiveis(
                self.usuario
            )

            self.assertEqual(
                {m.id for m in disponiveis},
                {m.id for m in self.materiais},
            )

            novo = servico.criar(
                self.usuario,
                self.materiais[0].id,
            )
            servico.adicionar_material(
                novo.id,
                self.materiais[1].id,
                self.usuario,
            )

        # A consulta do lote antigo preserva o vínculo atual.
        with conectar(self.caminho) as conexao:
            servico = self.servico_com_cotacao(conexao)
            antes = conexao.total_changes

            antigo = servico.buscar_do_usuario(
                lote.id,
                self.usuario,
            )

            self.assertIs(antigo.status, StatusLote.CANCELADO)
            self.assertEqual(antigo.pesoRegistrado, 9.5)
            self.assertEqual(len(antigo.materiais), 1)

            atual = antigo.materiais[0].loteAtual

            self.assertIsNotNone(atual)
            self.assertEqual(atual.id, novo.id)
            self.assertEqual(len(atual.materiais), 2)
            self.assertIs(
                antigo.materiais[0],
                atual.materiais[0],
            )
            self.assertEqual(conexao.total_changes, antes)


if __name__ == "__main__":
    unittest.main()