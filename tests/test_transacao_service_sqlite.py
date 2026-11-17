"""Persistência comercial: DAOs SQLite e TransacaoService em conjunto."""

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.dao.certificado_sqlite_dao import CertificadoSQLiteDAO
from app.dao.lote_sqlite_dao import LoteSQLiteDAO
from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
from app.dao.transacao_sqlite_dao import TransacaoSQLiteDAO
from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.database.seed import semear_demo
from app.model.enums import (
    CondicaoMaterial,
    StatusLote,
    StatusMaterial,
    StatusTransacao,
)
from app.model.servicos_ia import PrecificacaoIA
from app.services.lote_service import LoteService
from app.services.material_service import MaterialService
from app.services.transacao_service import TransacaoService


class BaseComercial(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp())
        self.caminho = self.pasta / "t.sqlite3"
        inicializar_banco(self.caminho)
        with conectar(self.caminho) as conexao:
            semear_demo(conexao)

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def servicos(self, conexao):
        precificacao = PrecificacaoIA(2.75)
        return (
            MaterialService(
                MaterialSQLiteDAO(conexao), TipoMaterialSQLiteDAO(conexao)
            ),
            LoteService(
                LoteSQLiteDAO(conexao), MaterialSQLiteDAO(conexao), precificacao
            ),
            TransacaoService(
                TransacaoSQLiteDAO(conexao),
                LoteSQLiteDAO(conexao),
                precificacao,
                CertificadoSQLiteDAO(conexao),
            ),
            UsuarioSQLiteDAO(conexao),
        )

    def preparar_lote_disponivel(self, conexao, pesos=(4, 6), pesagem=9.5):
        materiais, lotes, _, usuarios = self.servicos(conexao)
        carlos = usuarios.buscar_por_email("carlos@email.com")
        tipo = TipoMaterialSQLiteDAO(conexao).listar()[0]
        lote = None
        for peso in pesos:
            material = materiais.registrar(
                carlos, tipo, peso, CondicaoMaterial.LIMPO
            )
            materiais.disponibilizar(material.id, carlos)
            if lote is None:
                lote = lotes.criar(carlos, material.id)
            else:
                lotes.adicionar_material(lote.id, material.id, carlos)
        if pesagem:
            lotes.registrar_pesagem(lote.id, carlos, pesagem)
        lotes.disponibilizar(lote.id, carlos)
        return carlos, lote.id


class TestPropostasPersistidas(BaseComercial):
    def test_proposta_e_recuperada_com_lote_e_participantes(self):
        with conectar(self.caminho) as conexao:
            carlos, lote_id = self.preparar_lote_disponivel(conexao)
            _, _, transacoes, usuarios = self.servicos(conexao)
            empresa = usuarios.buscar_por_email("empresa@email.com")
            proposta = transacoes.propor(lote_id, empresa, 30.0)
            id_proposta = proposta.id

        with conectar(self.caminho) as conexao:
            _, _, transacoes, usuarios = self.servicos(conexao)
            empresa = usuarios.buscar_por_email("empresa@email.com")
            carlos = usuarios.buscar_por_email("carlos@email.com")
            [proposta] = transacoes.listar_propostas(empresa)
            self.assertEqual(proposta.id, id_proposta)
            self.assertEqual(proposta.status, StatusTransacao.PENDENTE)
            self.assertEqual(proposta.valorTotal, 30.0)
            self.assertIs(proposta.vendedor, proposta.lote.criador)
            self.assertEqual(proposta.vendedor.id, carlos.id)
            self.assertEqual(proposta.lote.transacoes, [proposta])
            self.assertEqual(len(transacoes.listar_vendas(carlos)), 1)

    def test_comprador_nao_propoe_ao_proprio_lote_nem_duas_vezes(self):
        with conectar(self.caminho) as conexao:
            carlos, lote_id = self.preparar_lote_disponivel(conexao)
            _, _, transacoes, usuarios = self.servicos(conexao)
            empresa = usuarios.buscar_por_email("empresa@email.com")
            transacoes.propor(lote_id, empresa, 30.0)

            with self.assertRaises(ValueError):
                transacoes.propor(lote_id, empresa, 31.0)

            # O catador não é perfil comprador.
            with self.assertRaises(PermissionError):
                transacoes.propor(lote_id, carlos, 10.0)

        with conectar(self.caminho) as conexao:
            self.assertEqual(
                conexao.execute("SELECT COUNT(*) FROM transacoes").fetchone()[0], 1
            )

    def test_mercado_exclui_lote_proprio_mesmo_com_instancias_diferentes(self):
        with conectar(self.caminho) as conexao:
            self.preparar_lote_disponivel(conexao)
            _, _, transacoes, usuarios = self.servicos(conexao)
            empresa = usuarios.buscar_por_email("empresa@email.com")
            self.assertEqual(len(transacoes.listar_mercado(empresa)), 1)


class TestConclusaoAtomica(BaseComercial):
    def propor_e_concluir(self, comprador_email):
        with conectar(self.caminho) as conexao:
            carlos, lote_id = self.preparar_lote_disponivel(conexao)
            _, _, transacoes, usuarios = self.servicos(conexao)
            comprador = usuarios.buscar_por_email(comprador_email)
            proposta = transacoes.propor(lote_id, comprador, 30.0)
            outra = transacoes.propor(
                lote_id, usuarios.buscar_por_email("cooperativa@email.com"), 25.0
            ) if comprador_email != "cooperativa@email.com" else None

        with conectar(self.caminho) as conexao:
            _, _, transacoes, usuarios = self.servicos(conexao)
            carlos = usuarios.buscar_por_email("carlos@email.com")
            transacoes.concluir(proposta.id, carlos)

        return lote_id, proposta.id, (outra.id if outra else None)

    def test_conclusao_com_empresa_libera_materiais_e_cancela_concorrente(self):
        lote_id, id_proposta, id_outra = self.propor_e_concluir("empresa@email.com")

        with conectar(self.caminho) as conexao:
            _, lotes, transacoes, usuarios = self.servicos(conexao)
            empresa = usuarios.buscar_por_email("empresa@email.com")
            carlos = usuarios.buscar_por_email("carlos@email.com")

            lote = LoteSQLiteDAO(conexao).buscar_por_id(lote_id)
            self.assertEqual(lote.status, StatusLote.NEGOCIADO)
            self.assertEqual(
                sorted(t.status.value for t in lote.transacoes),
                ["CANCELADA", "CONCLUIDA"],
            )
            concluida = next(
                t for t in lote.transacoes if t.status == StatusTransacao.CONCLUIDA
            )
            self.assertEqual(concluida.id, id_proposta)
            self.assertEqual(concluida.pesoNegociado, 9.5)

            recebidos = MaterialSQLiteDAO(conexao).listar_por_responsavel(empresa)
            self.assertEqual(len(recebidos), 2)
            for material in recebidos:
                self.assertEqual(material.status, StatusMaterial.DISPONIVEL)
                self.assertEqual(
                    [e.tipo.value for e in material.obterHistorico()],
                    ["REGISTRO", "AGRUPAMENTO_LOTE", "TRANSFERENCIA"],
                )
            self.assertEqual(
                MaterialSQLiteDAO(conexao).listar_por_responsavel(carlos), []
            )
            self.assertEqual(
                conexao.execute(
                    "SELECT COUNT(*) FROM vinculos_lotes_atuais"
                ).fetchone()[0],
                0,
            )

    def test_conclusao_com_industria_destina_materiais(self):
        _, _, _ = self.propor_e_concluir("industria@email.com")

        with conectar(self.caminho) as conexao:
            _, _, _, usuarios = self.servicos(conexao)
            industria = usuarios.buscar_por_email("industria@email.com")
            recebidos = MaterialSQLiteDAO(conexao).listar_por_responsavel(industria)
            self.assertEqual(len(recebidos), 2)
            for material in recebidos:
                self.assertEqual(material.status, StatusMaterial.DESTINADO)
                self.assertEqual(
                    material.obterHistorico()[-1].tipo.value, "DESTINACAO"
                )

    def test_peso_negociado_nao_muda_quando_materiais_mudam_depois(self):
        lote_id, id_proposta, _ = self.propor_e_concluir("empresa@email.com")
        with conectar(self.caminho) as conexao:
            conexao.execute("UPDATE materiais SET peso_kg = 1")
        with conectar(self.caminho) as conexao:
            transacao = TransacaoSQLiteDAO(conexao).buscar_por_id(id_proposta)
            self.assertEqual(transacao.pesoNegociado, 9.5)

    def test_falha_sql_durante_conclusao_nao_deixa_alteracao_parcial(self):
        with conectar(self.caminho) as conexao:
            carlos, lote_id = self.preparar_lote_disponivel(conexao)
            _, _, transacoes, usuarios = self.servicos(conexao)
            empresa = usuarios.buscar_por_email("empresa@email.com")
            proposta = transacoes.propor(lote_id, empresa, 30.0)

        def instantaneo(conexao):
            return {
                "materiais": [tuple(r) for r in conexao.execute(
                    "SELECT id, status, responsavel_atual_id FROM materiais ORDER BY id")],
                "eventos": conexao.execute(
                    "SELECT COUNT(*) FROM eventos_rastreio").fetchone()[0],
                "vinculos": conexao.execute(
                    "SELECT COUNT(*) FROM vinculos_lotes_atuais").fetchone()[0],
                "lote": conexao.execute("SELECT status FROM lotes").fetchone()[0],
                "transacoes": [tuple(r) for r in conexao.execute(
                    "SELECT id, status, peso_negociado FROM transacoes")],
            }

        with conectar(self.caminho) as conexao:
            antes = instantaneo(conexao)

        with conectar(self.caminho) as conexao:
            _, _, transacoes, usuarios = self.servicos(conexao)
            carlos = usuarios.buscar_por_email("carlos@email.com")
            # Falha provocada no último passo (marcar o lote NEGOCIADO),
            # depois de materiais e vínculos já terem sido alterados.
            conexao.execute(
                "CREATE TEMP TRIGGER falha BEFORE UPDATE OF status ON lotes "
                "WHEN NEW.status = 'NEGOCIADO' "
                "BEGIN SELECT RAISE(ABORT, 'falha provocada'); END"
            )
            with self.assertRaises(sqlite3.DatabaseError):
                transacoes.concluir(proposta.id, carlos)

            # Mesmo que o chamador capture o erro e confirme a transação
            # externa, o SAVEPOINT já desfez tudo.
            self.assertEqual(instantaneo(conexao), antes)

        with conectar(self.caminho) as conexao:
            self.assertEqual(instantaneo(conexao), antes)


class TestCertificadoPersistido(BaseComercial):
    def test_certificado_exige_conclusao_e_e_unico(self):
        with conectar(self.caminho) as conexao:
            carlos, lote_id = self.preparar_lote_disponivel(conexao)
            _, _, transacoes, usuarios = self.servicos(conexao)
            empresa = usuarios.buscar_por_email("empresa@email.com")
            proposta = transacoes.propor(lote_id, empresa, 30.0)

            with self.assertRaises(ValueError):
                transacoes.emitir_certificado(proposta.id, carlos)

            transacoes.concluir(proposta.id, carlos)
            certificado = transacoes.emitir_certificado(proposta.id, carlos)

            with self.assertRaises(ValueError):
                transacoes.emitir_certificado(proposta.id, carlos)

            self.assertEqual(
                conexao.execute("SELECT COUNT(*) FROM certificados").fetchone()[0], 1
            )

        with conectar(self.caminho) as conexao:
            _, _, transacoes, usuarios = self.servicos(conexao)
            empresa = usuarios.buscar_por_email("empresa@email.com")
            cooperativa = usuarios.buscar_por_email("cooperativa@email.com")

            recuperado, transacao = transacoes.consultar_certificado(
                certificado.id, empresa
            )
            self.assertEqual(recuperado.id, certificado.id)
            self.assertEqual(recuperado.codigo, certificado.codigo)
            self.assertEqual(transacao.id, proposta.id)
            self.assertEqual(transacao.certificado.id, certificado.id)

            with self.assertRaises(PermissionError):
                transacoes.consultar_certificado(certificado.id, cooperativa)


class TestLoteCancelado(BaseComercial):
    def test_cancelar_lote_cancela_pendentes_no_banco(self):
        with conectar(self.caminho) as conexao:
            carlos, lote_id = self.preparar_lote_disponivel(conexao)
            _, lotes, transacoes, usuarios = self.servicos(conexao)
            transacoes.propor(
                lote_id, usuarios.buscar_por_email("empresa@email.com"), 30.0
            )
            lotes.cancelar(lote_id, carlos)

        with conectar(self.caminho) as conexao:
            self.assertEqual(
                conexao.execute("SELECT status FROM transacoes").fetchone()[0],
                "CANCELADA",
            )
            lote = LoteSQLiteDAO(conexao).buscar_por_id(lote_id)
            self.assertEqual(lote.status, StatusLote.CANCELADO)
            [t] = lote.transacoes
            self.assertEqual(t.status, StatusTransacao.CANCELADA)

    def test_pesagem_de_lote_disponivel_com_proposta_pendente(self):
        with conectar(self.caminho) as conexao:
            carlos, lote_id = self.preparar_lote_disponivel(conexao)
            _, lotes, transacoes, usuarios = self.servicos(conexao)
            transacoes.propor(
                lote_id, usuarios.buscar_por_email("empresa@email.com"), 30.0
            )
            lotes.registrar_pesagem(lote_id, carlos, 9.0)

        with conectar(self.caminho) as conexao:
            lote = LoteSQLiteDAO(conexao).buscar_por_id(lote_id)
            self.assertEqual(lote.pesoRegistrado, 9.0)
            self.assertEqual(len(lote.transacoes), 1)


if __name__ == "__main__":
    unittest.main()
