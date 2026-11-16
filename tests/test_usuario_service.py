import unittest
from types import SimpleNamespace

from werkzeug.security import generate_password_hash

from app.dao.usuario_dao import UsuarioDAO
from app.model.usuario import UsuarioComum
from app.services.usuario_service import (
    UsuarioService,
    CredenciaisInvalidasError,
)


class TestUsuarioService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.senha_hash = generate_password_hash(
            "SenhaTeste123"
        )

    def setUp(self):
        self.usuario = UsuarioComum(
            nome="Pessoa de teste",
            email="pessoa@example.com",
            senhaHash=self.senha_hash,
            telefone="00000000000",
            endereco="Endereço de teste",
        )

        self.repositorio = SimpleNamespace(
            usuarios=[self.usuario]
        )
        self.servico = UsuarioService(
            UsuarioDAO(self.repositorio)
        )

    def test_autenticacao_com_credenciais_validas(self):
        encontrado = self.servico.autenticar(
            "pessoa@example.com",
            "SenhaTeste123",
        )

        self.assertIs(encontrado, self.usuario)

    def test_email_normalizado_no_login(self):
        encontrado = self.servico.autenticar(
            "  PESSOA@EXAMPLE.COM  ",
            "SenhaTeste123",
        )

        self.assertIs(encontrado, self.usuario)

    def test_senha_incorreta_ou_email_inexistente(self):
        casos = [
            ("pessoa@example.com", "senha-incorreta"),
            ("inexistente@example.com", "SenhaTeste123"),
        ]

        for email, senha in casos:
            with self.subTest(email=email):
                with self.assertRaisesRegex(
                    CredenciaisInvalidasError,
                    "E-mail ou senha inválidos",
                ):
                    self.servico.autenticar(email, senha)

    def test_busca_usuario_por_id(self):
        encontrado = self.servico.buscar_por_id(
            str(self.usuario.id)
        )

        self.assertIs(encontrado, self.usuario)

    def test_id_ausente_ou_inexistente_retorna_none(self):
        self.assertIsNone(
            self.servico.buscar_por_id(None)
        )
        self.assertIsNone(
            self.servico.buscar_por_id("id-inexistente")
        )


if __name__ == "__main__":
    unittest.main()