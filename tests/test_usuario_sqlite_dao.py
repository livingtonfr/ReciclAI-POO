import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.model.enums import StatusValidacao
from app.model.usuario import (
    PERFIS_USUARIO,
    Usuario,
    UsuarioComum,
)
from app.services.usuario_service import (
    UsuarioService,
    CredenciaisInvalidasError,
)


class TestUsuarioSQLiteDAO(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hash_senha = generate_password_hash("senha123")

    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)

        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

    def criar(self, email="teste@example.com"):
        return UsuarioComum(
            "Teste",
            email,
            self.hash_senha,
            "000",
            "Rua Teste",
        )

    def test_reconstroi_cinco_perfis_e_preserva_dados(self):
        for perfil, (classe, documento) in PERFIS_USUARIO.items():
            with self.subTest(perfil=perfil):
                dados = dict(
                    perfil=perfil,
                    identificador=str(uuid4()),
                    nome="Teste",
                    email=f"{perfil}@example.com",
                    senhaHash=self.hash_senha,
                    telefone="000",
                    endereco="Rua Teste",
                    criadoEm="2020-01-02T03:04:05.123456",
                    latitude=-16.68,
                    longitude=-49.25,
                )

                if documento == "cpf":
                    dados["cpf"] = "00000000000"
                elif documento == "cnpj":
                    dados["cnpj"] = "00000000000000"
                    dados["statusValidacao"] = "APROVADA"

                original = Usuario.reconstituir(**dados)

                with conectar(self.caminho) as conexao:
                    UsuarioSQLiteDAO(conexao).adicionar(original)

                with conectar(self.caminho) as conexao:
                    recuperado = UsuarioSQLiteDAO(
                        conexao
                    ).buscar_por_id(original.id)

                self.assertIs(type(recuperado), classe)

                for campo in (
                    "id", "nome", "email", "senhaHash",
                    "telefone", "endereco", "criadoEm",
                    "latitude", "longitude",
                ):
                    self.assertEqual(
                        getattr(recuperado, campo),
                        getattr(original, campo),
                    )

                if documento:
                    self.assertEqual(
                        getattr(recuperado, documento),
                        getattr(original, documento),
                    )

                if documento == "cnpj":
                    self.assertIs(
                        recuperado.statusValidacao,
                        StatusValidacao.APROVADA,
                    )

    def test_autenticacao_apos_reabrir(self):
        with conectar(self.caminho) as conexao:
            usuario = UsuarioService(
                UsuarioSQLiteDAO(conexao)
            ).cadastrar(
                "comum",
                "Teste",
                " LOGIN@example.com ",
                "senha123",
                "000",
                "Rua",
            )

        with conectar(self.caminho) as conexao:
            service = UsuarioService(UsuarioSQLiteDAO(conexao))

            recuperado = service.autenticar(
                " LOGIN@EXAMPLE.COM ",
                "senha123",
            )

            self.assertEqual(recuperado.id, usuario.id)
            self.assertEqual(
                recuperado.senhaHash, usuario.senhaHash
            )
            self.assertNotEqual(
                recuperado.senhaHash, "senha123"
            )

            with self.assertRaises(CredenciaisInvalidasError):
                service.autenticar(
                    "login@example.com", "errada"
                )

    def test_recusa_email_duplicado_e_reverte_nova_transacao(self):
        with conectar(self.caminho) as conexao:
            UsuarioSQLiteDAO(conexao).adicionar(self.criar())

        with self.assertRaisesRegex(ValueError, "e-mail"):
            with conectar(self.caminho) as conexao:
                dao = UsuarioSQLiteDAO(conexao)

                dao.adicionar(
                    self.criar("outro@example.com")
                )
                dao.adicionar(
                    self.criar(" TESTE@EXAMPLE.COM ")
                )

        with conectar(self.caminho) as conexao:
            dao = UsuarioSQLiteDAO(conexao)

            self.assertIsNone(
                dao.buscar_por_email("outro@example.com")
            )
            self.assertIsNotNone(
                dao.buscar_por_email("teste@example.com")
            )

    def test_recusa_id_duplicado(self):
        usuario = self.criar()

        with conectar(self.caminho) as conexao:
            UsuarioSQLiteDAO(conexao).adicionar(usuario)

        with self.assertRaisesRegex(
            ValueError, "já está cadastrado"
        ):
            with conectar(self.caminho) as conexao:
                UsuarioSQLiteDAO(conexao).adicionar(usuario)

    def test_consultas_inexistentes(self):
        with conectar(self.caminho) as conexao:
            dao = UsuarioSQLiteDAO(conexao)
            dao.adicionar(self.criar())

            self.assertIsNone(dao.buscar_por_id(None))
            self.assertIsNone(dao.buscar_por_id(uuid4()))
            self.assertIsNone(
                dao.buscar_por_email("ausente@example.com")
            )
            self.assertIsNone(
                dao.buscar_por_email("' OR 1=1 --")
            )


if __name__ == "__main__":
    unittest.main()