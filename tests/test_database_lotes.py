import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.model.enums import CategoriaMaterial, CondicaoMaterial
from app.model.material import Material, TipoMaterial
from app.model.usuario import Catador


class TestDatabaseLotes(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

        tipo = TipoMaterial(
            "PET", "Teste", CategoriaMaterial.PLASTICO
        )
        self.usuario = Catador(
            "Teste", "teste@example.com", "hash",
            "000", "Rua", "00000000000",
        )
        self.material = Material(
            tipo, 10, CondicaoMaterial.LIMPO, self.usuario
        )
        self.lote_id = str(uuid4())

        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(tipo)
            UsuarioSQLiteDAO(conexao).adicionar(self.usuario)
            MaterialSQLiteDAO(conexao).adicionar(self.material)
            self.inserir_lote(conexao, self.lote_id)

    def inserir_lote(
        self, conexao, lote_id, peso=None, status="EM_FORMACAO"
    ):
        conexao.execute(
            "INSERT INTO lotes "
            "(id, criador_id, data_criacao, status, peso_registrado) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                lote_id,
                str(self.usuario.id),
                "2026-01-01T10:00:00",
                status,
                peso,
            ),
        )

    def compor(
        self, conexao, lote_id, material_id=None, ordem=0
    ):
        conexao.execute(
            "INSERT INTO lotes_materiais "
            "(lote_id, material_id, ordem) VALUES (?, ?, ?)",
            (
                lote_id,
                material_id or str(self.material.id),
                ordem,
            ),
        )

    def vincular(self, conexao, lote_id):
        conexao.execute(
            "INSERT INTO vinculos_lotes_atuais "
            "(material_id, lote_id) VALUES (?, ?)",
            (str(self.material.id), lote_id),
        )

    def test_reinicializacao_preserva_lote_e_composicao(self):
        with conectar(self.caminho) as conexao:
            self.compor(conexao, self.lote_id)

        inicializar_banco(self.caminho)

        with conectar(self.caminho) as conexao:
            lote = conexao.execute(
                "SELECT * FROM lotes WHERE id = ?",
                (self.lote_id,),
            ).fetchone()

            self.assertIsNone(lote["peso_registrado"])
            self.assertEqual(lote["status"], "EM_FORMACAO")

            total = conexao.execute(
                "SELECT COUNT(*) FROM lotes_materiais"
            ).fetchone()[0]

            self.assertEqual(total, 1)

    def test_recusa_pesos_e_estados_invalidos(self):
        with conectar(self.caminho) as conexao:
            for peso in (0, -1, 50001, float("inf")):
                with self.subTest(peso=peso):
                    with self.assertRaises(sqlite3.IntegrityError):
                        self.inserir_lote(
                            conexao, str(uuid4()), peso=peso
                        )

            with self.assertRaises(sqlite3.IntegrityError):
                self.inserir_lote(
                    conexao, str(uuid4()), status="INVALIDO"
                )

            self.inserir_lote(
                conexao, str(uuid4()), peso=50000
            )

    def test_recusa_referencias_inexistentes(self):
        with conectar(self.caminho) as conexao:
            with self.assertRaises(sqlite3.IntegrityError):
                self.compor(conexao, str(uuid4()))

            with self.assertRaises(sqlite3.IntegrityError):
                self.compor(
                    conexao,
                    self.lote_id,
                    material_id=str(uuid4()),
                )

            with self.assertRaises(sqlite3.IntegrityError):
                self.vincular(conexao, self.lote_id)

    def test_recusa_ordem_invalida_e_material_repetido(self):
        with conectar(self.caminho) as conexao:
            for ordem in (-1, 0.5):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.compor(
                        conexao, self.lote_id, ordem=ordem
                    )

            self.compor(conexao, self.lote_id)

            with self.assertRaises(sqlite3.IntegrityError):
                self.compor(
                    conexao, self.lote_id, ordem=1
                )

    def test_preserva_composicao_antiga_e_impede_dois_vinculos(self):
        novo_id = str(uuid4())

        with conectar(self.caminho) as conexao:
            self.inserir_lote(conexao, novo_id)
            self.compor(conexao, self.lote_id)
            self.compor(conexao, novo_id)
            self.vincular(conexao, self.lote_id)

            with self.assertRaises(sqlite3.IntegrityError):
                self.vincular(conexao, novo_id)

            conexao.execute(
                "DELETE FROM vinculos_lotes_atuais "
                "WHERE material_id = ?",
                (str(self.material.id),),
            )
            self.vincular(conexao, novo_id)

            total = conexao.execute(
                "SELECT COUNT(*) FROM lotes_materiais"
            ).fetchone()[0]

            self.assertEqual(total, 2)

    def test_falha_reverte_lote_e_composicao(self):
        novo_id = str(uuid4())

        with self.assertRaises(RuntimeError):
            with conectar(self.caminho) as conexao:
                self.inserir_lote(conexao, novo_id)
                self.compor(conexao, novo_id)
                raise RuntimeError("Falha posterior")

        with conectar(self.caminho) as conexao:
            lote = conexao.execute(
                "SELECT id FROM lotes WHERE id = ?",
                (novo_id,),
            ).fetchone()

            self.assertIsNone(lote)

            total = conexao.execute(
                "SELECT COUNT(*) FROM lotes_materiais"
            ).fetchone()[0]

            self.assertEqual(total, 0)


if __name__ == "__main__":
    unittest.main()