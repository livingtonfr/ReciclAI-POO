import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.model.enums import CategoriaMaterial


class TestInicializacaoSQLite(unittest.TestCase):
    def setUp(self):
        self.temporario = TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)

        self.caminho = (
            Path(self.temporario.name) / "teste.sqlite3"
        )

        inicializar_banco(self.caminho)

    def test_aceita_todas_as_categorias_do_modelo(self):
        with conectar(self.caminho) as conexao:
            for categoria in CategoriaMaterial:
                conexao.execute(
                    "INSERT INTO tipos_material "
                    "(id, nome, descricao, categoria) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        str(uuid4()),
                        categoria.value,
                        "Teste",
                        categoria.value,
                    ),
                )

            registros = conexao.execute(
                "SELECT * FROM tipos_material"
            ).fetchall()

            self.assertEqual(
                len(registros), len(CategoriaMaterial)
            )
            self.assertTrue(
                all(item["ativo"] == 1 for item in registros)
            )

    def test_reinicializacao_preserva_registro(self):
        identificador = str(uuid4())

        with conectar(self.caminho) as conexao:
            conexao.execute(
                "INSERT INTO tipos_material "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    identificador,
                    "PET",
                    "Plástico PET",
                    "PLASTICO",
                    0,
                ),
            )

        inicializar_banco(self.caminho)
        inicializar_banco(self.caminho)

        with conectar(self.caminho) as conexao:
            registros = conexao.execute(
                "SELECT * FROM tipos_material"
            ).fetchall()

            self.assertEqual(len(registros), 1)
            self.assertEqual(
                tuple(registros[0]),
                (
                    identificador,
                    "PET",
                    "Plástico PET",
                    "PLASTICO",
                    0,
                ),
            )

    def test_recusa_categoria_ativo_e_id_invalidos(self):
        casos = (
            (str(uuid4()), "INEXISTENTE", 1),
            (str(uuid4()), "PLASTICO", 2),
            (None, "PLASTICO", 1),
        )

        for identificador, categoria, ativo in casos:
            with self.subTest(
                categoria=categoria,
                ativo=ativo,
                id=identificador,
            ):
                with self.assertRaises(sqlite3.IntegrityError):
                    with conectar(self.caminho) as conexao:
                        conexao.execute(
                            "INSERT INTO tipos_material "
                            "VALUES (?, ?, ?, ?, ?)",
                            (
                                identificador,
                                "PET",
                                "Teste",
                                categoria,
                                ativo,
                            ),
                        )

        with conectar(self.caminho) as conexao:
            total = conexao.execute(
                "SELECT COUNT(*) FROM tipos_material"
            ).fetchone()[0]

            self.assertEqual(total, 0)


if __name__ == "__main__":
    unittest.main()