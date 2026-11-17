import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.dao.lote_sqlite_dao import LoteSQLiteDAO
from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.model.enums import (
    CategoriaMaterial,
    CondicaoMaterial,
    StatusLote,
    StatusMaterial,
)
from app.model.material import Material, TipoMaterial
from app.model.usuario import Catador


class TestLoteSQLiteCancelamento(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)

        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

        tipo = TipoMaterial(
            "PET", "Teste", CategoriaMaterial.PLASTICO
        )
        usuario = Catador(
            "Teste", "teste@example.com", "hash",
            "000", "Rua", "00000000000",
        )

        self.materiais = [
            Material(
                tipo,
                peso,
                CondicaoMaterial.LIMPO,
                usuario,
            )
            for peso in (10, 20)
        ]

        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(tipo)
            UsuarioSQLiteDAO(conexao).adicionar(usuario)

            for material in self.materiais:
                material.disponibilizar()
                MaterialSQLiteDAO(conexao).adicionar(material)

            self.lote = usuario.criarLote(self.materiais[0])
            self.lote.adicionarMaterial(self.materiais[1])
            self.lote.registrarPesagem(29)

            LoteSQLiteDAO(conexao).adicionar(self.lote)

    def conferir_ativo(self):
        with conectar(self.caminho) as conexao:
            lote = LoteSQLiteDAO(conexao).buscar_por_id(
                self.lote.id
            )

            self.assertIs(
                lote.status,
                StatusLote.EM_FORMACAO,
            )
            self.assertEqual(lote.pesoRegistrado, 29)

            for material in lote.materiais:
                self.assertIs(material.loteAtual, lote)
                self.assertIs(
                    material.status,
                    StatusMaterial.EM_LOTE,
                )

    def test_cancela_preservando_composicao_pesagem_e_eventos(self):
        with conectar(self.caminho) as conexao:
            lote = LoteSQLiteDAO(conexao).cancelar(
                self.lote.id
            )

            self.assertIs(lote.status, StatusLote.CANCELADO)
            self.assertTrue(
                all(m.loteAtual is None for m in lote.materiais)
            )

        with conectar(self.caminho) as conexao:
            registro = conexao.execute(
                "SELECT status, peso_registrado FROM lotes "
                "WHERE id = ?",
                (str(self.lote.id),),
            ).fetchone()

            self.assertEqual(registro["status"], "CANCELADO")
            self.assertEqual(registro["peso_registrado"], 29)

            composicao = conexao.execute(
                "SELECT COUNT(*) FROM lotes_materiais"
            ).fetchone()[0]

            vinculos = conexao.execute(
                "SELECT COUNT(*) FROM vinculos_lotes_atuais"
            ).fetchone()[0]

            self.assertEqual(composicao, 2)
            self.assertEqual(vinculos, 0)

            for original in self.materiais:
                material = MaterialSQLiteDAO(
                    conexao
                ).buscar_por_id(original.id)

                self.assertIs(
                    material.status,
                    StatusMaterial.DISPONIVEL,
                )
                self.assertEqual(
                    [e.id for e in material.obterHistorico()],
                    [e.id for e in original.obterHistorico()],
                )

    def test_cancela_lote_disponivel_e_recusa_repeticao(self):
        with conectar(self.caminho) as conexao:
            dao = LoteSQLiteDAO(conexao)
            lote = dao.buscar_por_id(self.lote.id)

            lote.disponibilizar()
            dao.atualizar_pesagem_e_estado(lote)
            dao.cancelar(lote.id)

            with self.assertRaises(ValueError):
                dao.cancelar(lote.id)

            with self.assertRaises(ValueError):
                dao.cancelar(uuid4())

            total = conexao.execute(
                "SELECT COUNT(*) FROM lotes_materiais"
            ).fetchone()[0]

            self.assertEqual(total, 2)

    def test_falha_sql_reverte_liberacao_dos_materiais(self):
        with conectar(self.caminho) as conexao:
            conexao.execute(
                "CREATE TEMP TRIGGER falhar_cancelamento "
                "BEFORE UPDATE OF status ON lotes "
                "BEGIN "
                "SELECT RAISE(ABORT, 'Falha simulada'); "
                "END"
            )

            with self.assertRaises(sqlite3.IntegrityError):
                LoteSQLiteDAO(conexao).cancelar(
                    self.lote.id
                )

        self.conferir_ativo()

    def test_falha_externa_reverte_cancelamento(self):
        with self.assertRaises(RuntimeError):
            with conectar(self.caminho) as conexao:
                LoteSQLiteDAO(conexao).cancelar(
                    self.lote.id
                )
                raise RuntimeError("Falha posterior")

        self.conferir_ativo()


if __name__ == "__main__":
    unittest.main()