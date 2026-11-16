import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.database.conexao import conectar


class TestConexaoSQLite(unittest.TestCase):
    def setUp(self):
        self.temporario = TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)

        self.caminho = (
            Path(self.temporario.name)
            / "instance"
            / "teste.sqlite3"
        )

    def test_gravacao_persiste_apos_reabrir(self):
        with conectar(self.caminho) as conexao:
            conexao.execute(
                "CREATE TABLE teste (nome TEXT NOT NULL)"
            )
            conexao.execute(
                "INSERT INTO teste (nome) VALUES (?)",
                ("PET",),
            )

        self.assertTrue(self.caminho.is_file())

        with conectar(self.caminho) as conexao:
            registro = conexao.execute(
                "SELECT nome FROM teste"
            ).fetchone()

            self.assertEqual(registro["nome"], "PET")

    def test_erro_reverte_gravacoes_e_fecha_conexao(self):
        with conectar(self.caminho) as conexao:
            conexao.execute(
                "CREATE TABLE teste (nome TEXT NOT NULL)"
            )

        with self.assertRaisesRegex(ValueError, "Falha simulada"):
            with conectar(self.caminho) as conexao:
                conexao.execute(
                    "INSERT INTO teste VALUES (?)",
                    ("PET",),
                )
                conexao.execute(
                    "INSERT INTO teste VALUES (?)",
                    ("Vidro",),
                )
                raise ValueError("Falha simulada")

        with self.assertRaises(sqlite3.ProgrammingError):
            conexao.execute("SELECT 1")

        with conectar(self.caminho) as outra:
            quantidade = outra.execute(
                "SELECT COUNT(*) FROM teste"
            ).fetchone()[0]

            self.assertEqual(quantidade, 0)

    def test_fecha_conexao_apos_sucesso(self):
        with conectar(self.caminho) as conexao:
            resultado = conexao.execute("SELECT 1").fetchone()
            self.assertEqual(resultado[0], 1)

        with self.assertRaises(sqlite3.ProgrammingError):
            conexao.execute("SELECT 1")

    def test_rejeita_referencia_inexistente(self):
        with conectar(self.caminho) as conexao:
            conexao.execute(
                "CREATE TABLE pai (id INTEGER PRIMARY KEY)"
            )
            conexao.execute(
                "CREATE TABLE filho "
                "(pai_id INTEGER REFERENCES pai(id))"
            )

        with self.assertRaises(sqlite3.IntegrityError):
            with conectar(self.caminho) as conexao:
                conexao.execute(
                    "INSERT INTO filho (pai_id) VALUES (?)",
                    (999,),
                )

    def test_aceita_banco_em_memoria(self):
        with conectar(":memory:") as conexao:
            resultado = conexao.execute("SELECT 1").fetchone()
            self.assertEqual(resultado[0], 1)

            chaves_estrangeiras = conexao.execute(
                "PRAGMA foreign_keys"
            ).fetchone()[0]

            self.assertEqual(chaves_estrangeiras, 1)


if __name__ == "__main__":
    unittest.main()