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
    StatusMaterial,
)
from app.model.material import Material, TipoMaterial
from app.model.usuario import Catador


class TestLoteSQLiteComposicao(unittest.TestCase):
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
            self.lote.registrarPesagem(10)

            LoteSQLiteDAO(conexao).adicionar(self.lote)

    def recuperar(self):
        with conectar(self.caminho) as conexao:
            return LoteSQLiteDAO(conexao).buscar_por_id(
                self.lote.id
            )

    def test_inclusao_persiste_evento_vinculo_e_invalida_peso(self):
        with conectar(self.caminho) as conexao:
            lote = LoteSQLiteDAO(conexao).adicionar_material(
                self.lote.id,
                self.materiais[1].id,
            )

            self.assertIs(
                lote.materiais[1].loteAtual,
                lote,
            )

        lote = self.recuperar()

        self.assertEqual(
            [m.id for m in lote.materiais],
            [m.id for m in self.materiais],
        )
        self.assertEqual(lote.calcularPesoTotal(), 30)
        self.assertIsNone(lote.pesoRegistrado)
        self.assertEqual(
            len(lote.materiais[1].obterHistorico()),
            2,
        )

    def test_remocao_libera_material_e_preserva_historico(self):
        with conectar(self.caminho) as conexao:
            dao = LoteSQLiteDAO(conexao)

            lote = dao.adicionar_material(
                self.lote.id,
                self.materiais[1].id,
            )
            lote.registrarPesagem(29)
            dao.atualizar_pesagem_e_estado(lote)

            dao.remover_material(
                lote.id,
                self.materiais[1].id,
            )

        with conectar(self.caminho) as conexao:
            material = MaterialSQLiteDAO(conexao).buscar_por_id(
                self.materiais[1].id
            )

            self.assertIs(
                material.status,
                StatusMaterial.DISPONIVEL,
            )
            self.assertIsNone(material.loteAtual)
            self.assertEqual(
                len(material.obterHistorico()),
                2,
            )

        self.assertIsNone(self.recuperar().pesoRegistrado)
        self.assertEqual(
            len(self.recuperar().materiais),
            1,
        )

    def test_recusas_preservam_pesagem_e_composicao(self):
        with conectar(self.caminho) as conexao:
            dao = LoteSQLiteDAO(conexao)

            with self.assertRaises(ValueError):
                dao.remover_material(
                    self.lote.id,
                    self.materiais[0].id,
                )

            with self.assertRaises(ValueError):
                dao.remover_material(
                    self.lote.id,
                    uuid4(),
                )

            with self.assertRaises(ValueError):
                dao.adicionar_material(
                    self.lote.id,
                    self.materiais[0].id,
                )

        self.assertEqual(
            self.recuperar().pesoRegistrado,
            10,
        )
        self.assertEqual(
            len(self.recuperar().materiais),
            1,
        )

    def test_falha_sql_reverte_vinculos_evento_e_pesagem(self):
        with conectar(self.caminho) as conexao:
            conexao.execute(
                "CREATE TEMP TRIGGER falhar_peso "
                "BEFORE UPDATE OF peso_registrado ON lotes "
                "BEGIN "
                "SELECT RAISE(ABORT, 'Falha simulada'); "
                "END"
            )

            with self.assertRaises(sqlite3.IntegrityError):
                LoteSQLiteDAO(conexao).adicionar_material(
                    self.lote.id,
                    self.materiais[1].id,
                )

        self.assertEqual(
            self.recuperar().pesoRegistrado,
            10,
        )
        self.assertEqual(
            len(self.recuperar().materiais),
            1,
        )

        with conectar(self.caminho) as conexao:
            material = MaterialSQLiteDAO(conexao).buscar_por_id(
                self.materiais[1].id
            )

            self.assertIs(
                material.status,
                StatusMaterial.DISPONIVEL,
            )
            self.assertEqual(
                len(material.obterHistorico()),
                1,
            )

            total = conexao.execute(
                "SELECT COUNT(*) FROM vinculos_lotes_atuais"
            ).fetchone()[0]

            self.assertEqual(total, 1)

    def test_rollback_externo_reverte_composicao(self):
        with self.assertRaises(RuntimeError):
            with conectar(self.caminho) as conexao:
                LoteSQLiteDAO(conexao).adicionar_material(
                    self.lote.id,
                    self.materiais[1].id,
                )

                raise RuntimeError("Falha posterior")

        self.assertEqual(
            self.recuperar().pesoRegistrado,
            10,
        )
        self.assertEqual(
            len(self.recuperar().materiais),
            1,
        )


if __name__ == "__main__":
    unittest.main()