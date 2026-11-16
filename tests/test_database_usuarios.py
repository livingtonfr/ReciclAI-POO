import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco


class TestTabelaUsuarios(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)

        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

    def inserir(
        self,
        perfil="comum",
        email="teste@example.com",
        cpf=None,
        cnpj=None,
        status=None,
    ):
        identificador = str(uuid4())

        with conectar(self.caminho) as conexao:
            conexao.execute(
                "INSERT INTO usuarios "
                "(id, perfil, nome, email, senha_hash, telefone, "
                "endereco, criado_em, cpf, cnpj, status_validacao) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    identificador,
                    perfil,
                    "Teste",
                    email,
                    "hash-ficticio",
                    "00000000000",
                    "Endereco de teste",
                    "2026-11-16T12:00:00",
                    cpf,
                    cnpj,
                    status,
                ),
            )

        return identificador

    def test_aceita_os_cinco_perfis(self):
        self.inserir(email="comum@example.com")

        self.inserir(
            "catador",
            "catador@example.com",
            cpf="00000000000",
        )

        for perfil in ("cooperativa", "empresa", "industria"):
            self.inserir(
                perfil,
                f"{perfil}@example.com",
                cnpj="00000000000000",
                status="PENDENTE",
            )

        with conectar(self.caminho) as conexao:
            total = conexao.execute(
                "SELECT COUNT(*) FROM usuarios"
            ).fetchone()[0]

            self.assertEqual(total, 5)

    def test_recusa_email_duplicado(self):
        self.inserir(email="teste@example.com")

        with self.assertRaises(sqlite3.IntegrityError):
            self.inserir(email="TESTE@example.com")

    def test_recusa_perfil_e_documentos_incompativeis(self):
        casos = (
            {"perfil": "administrador"},
            {"perfil": "comum", "cpf": "123"},
            {"perfil": "catador"},
            {"perfil": "catador", "cpf": "   "},
            {"perfil": "empresa", "cnpj": "123"},
            {
                "perfil": "empresa",
                "cnpj": "123",
                "status": "INVALIDO",
            },
            {
                "perfil": "industria",
                "status": "PENDENTE",
            },
        )

        for caso in casos:
            with self.subTest(caso=caso):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.inserir(**caso)

        with conectar(self.caminho) as conexao:
            total = conexao.execute(
                "SELECT COUNT(*) FROM usuarios"
            ).fetchone()[0]

            self.assertEqual(total, 0)

    def test_reinicializacao_preserva_usuario_e_tipo(self):
        identificador = self.inserir()
        tipo_id = str(uuid4())

        with conectar(self.caminho) as conexao:
            conexao.execute(
                "INSERT INTO tipos_material "
                "VALUES (?, ?, ?, ?, ?)",
                (tipo_id, "PET", "Teste", "PLASTICO", 1),
            )

        inicializar_banco(self.caminho)

        with conectar(self.caminho) as conexao:
            usuario_id = conexao.execute(
                "SELECT id FROM usuarios"
            ).fetchall()[0][0]

            material_id = conexao.execute(
                "SELECT id FROM tipos_material"
            ).fetchall()[0][0]

            self.assertEqual(usuario_id, identificador)
            self.assertEqual(material_id, tipo_id)


if __name__ == "__main__":
    unittest.main()