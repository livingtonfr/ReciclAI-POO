import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.model.enums import CategoriaMaterial
from app.model.material import TipoMaterial


class TestTipoMaterialSQLiteDAO(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)

        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

        self.tipo = TipoMaterial(
            "PET",
            "Plástico PET",
            CategoriaMaterial.PLASTICO,
        )

    def test_persiste_e_reconstroi_apos_reabrir(self):
        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(self.tipo)

        with conectar(self.caminho) as conexao:
            dao = TipoMaterialSQLiteDAO(conexao)
            recuperado = dao.buscar_por_id(self.tipo.id)

            self.assertIsNot(recuperado, self.tipo)
            self.assertEqual(recuperado.id, self.tipo.id)
            self.assertEqual(recuperado.nome, self.tipo.nome)
            self.assertEqual(
                recuperado.descricao, self.tipo.descricao
            )
            self.assertIs(
                recuperado.categoria,
                CategoriaMaterial.PLASTICO,
            )
            self.assertIs(recuperado.ativo, True)
            self.assertEqual(
                [tipo.id for tipo in dao.listar()],
                [self.tipo.id],
            )

    def test_preserva_tipo_inativo(self):
        tipo = TipoMaterial.reconstituir(
            str(uuid4()),
            "Vidro",
            "Teste",
            "VIDRO",
            False,
        )

        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(tipo)

        with conectar(self.caminho) as conexao:
            recuperado = TipoMaterialSQLiteDAO(
                conexao
            ).buscar_por_id(str(tipo.id))

            self.assertEqual(recuperado.id, tipo.id)
            self.assertIs(recuperado.ativo, False)

    def test_busca_inexistente_e_consulta_parametrizada(self):
        with conectar(self.caminho) as conexao:
            dao = TipoMaterialSQLiteDAO(conexao)

            self.assertEqual(dao.listar(), [])
            dao.adicionar(self.tipo)

            self.assertIsNone(dao.buscar_por_id(uuid4()))
            self.assertIsNone(
                dao.buscar_por_id("' OR 1=1 --")
            )

    def test_duplicidade_reverte_transacao_sem_alterar_dados_anteriores(self):
        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(self.tipo)

        outro = TipoMaterial(
            "Papel",
            "Teste",
            CategoriaMaterial.PAPEL,
        )

        with self.assertRaises(sqlite3.IntegrityError):
            with conectar(self.caminho) as conexao:
                dao = TipoMaterialSQLiteDAO(conexao)
                dao.adicionar(outro)
                dao.adicionar(self.tipo)

        with conectar(self.caminho) as conexao:
            dao = TipoMaterialSQLiteDAO(conexao)

            self.assertIsNone(dao.buscar_por_id(outro.id))
            self.assertEqual(
                [tipo.id for tipo in dao.listar()],
                [self.tipo.id],
            )


if __name__ == "__main__":
    unittest.main()