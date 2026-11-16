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

    def dados_cadastro(self):
        return {
            "perfil": "comum",
            "nome": "Nova pessoa",
            "email": "nova@example.com",
            "senha": "SenhaNova123",
            "telefone": "00000000000",
            "endereco": "Novo endereço",
            "documento": "",
        }

    def test_cadastro_dos_cinco_perfis(self):
        for perfil, configuracao in (
            UsuarioService.PERFIS_CADASTRO.items()
        ):
            with self.subTest(perfil=perfil):
                classe, campo_documento = configuracao
                dados = self.dados_cadastro()
                dados["perfil"] = perfil
                dados["email"] = f"  {perfil.upper()}@EXAMPLE.COM  "

                if campo_documento is not None:
                    dados["documento"] = "00000000000000"

                usuario = self.servico.cadastrar(**dados)

                self.assertIsInstance(usuario, classe)
                self.assertEqual(
                    usuario.email,
                    f"{perfil}@example.com",
                )
                self.assertTrue(
                    usuario.verificarSenha("SenhaNova123")
                )
                self.assertFalse(
                    usuario.verificarSenha("senha-errada")
                )
                self.assertIn(
                    usuario,
                    self.repositorio.usuarios,
                )

    def test_cadastro_recusa_email_duplicado(self):
        dados = self.dados_cadastro()
        dados["email"] = "  PESSOA@EXAMPLE.COM  "

        with self.assertRaises(ValueError):
            self.servico.cadastrar(**dados)

        self.assertEqual(
            self.repositorio.usuarios,
            [self.usuario],
        )

    def test_cadastro_recusa_dados_invalidos(self):
        casos = [
            {"nome": "   "},
            {"email": "sem-arroba"},
            {"senha": "123"},
            {"perfil": "inexistente"},
            {"perfil": "catador", "documento": ""},
        ]

        for alteracoes in casos:
            with self.subTest(alteracoes=alteracoes):
                dados = self.dados_cadastro()
                dados.update(alteracoes)

                with self.assertRaises(ValueError):
                    self.servico.cadastrar(**dados)

                self.assertEqual(
                    self.repositorio.usuarios,
                    [self.usuario],
                )

    def test_atualizacao_de_perfil_normaliza_campos(self):
        atualizado = self.servico.atualizar_perfil(
            self.usuario,
            nome="  Nome atualizado  ",
            email="  ATUALIZADO@EXAMPLE.COM  ",
            telefone="  11111111111  ",
            endereco="  Endereço atualizado  ",
        )

        self.assertIs(atualizado, self.usuario)
        self.assertEqual(self.usuario.nome, "Nome atualizado")
        self.assertEqual(
            self.usuario.email,
            "atualizado@example.com",
        )
        self.assertEqual(self.usuario.telefone, "11111111111")
        self.assertEqual(
            self.usuario.endereco,
            "Endereço atualizado",
        )
        self.assertIs(
            self.servico.autenticar(
                "atualizado@example.com",
                "SenhaTeste123",
            ),
            self.usuario,
        )

    def test_email_duplicado_preserva_perfil_anterior(self):
        outra_pessoa = UsuarioComum(
            "Outra pessoa",
            "outra@example.com",
            self.senha_hash,
            "11111111111",
            "Outro endereço",
        )
        self.repositorio.usuarios.append(outra_pessoa)

        anterior = (
            self.usuario.nome,
            self.usuario.email,
            self.usuario.telefone,
            self.usuario.endereco,
        )

        with self.assertRaises(ValueError):
            self.servico.atualizar_perfil(
                self.usuario,
                nome="Nome que não deve ser salvo",
                email="OUTRA@EXAMPLE.COM",
                telefone="22222222222",
                endereco="Endereço que não deve ser salvo",
            )

        self.assertEqual(
            (
                self.usuario.nome,
                self.usuario.email,
                self.usuario.telefone,
                self.usuario.endereco,
            ),
            anterior,
        )

    def test_perfil_pode_manter_o_proprio_email(self):
        self.servico.atualizar_perfil(
            self.usuario,
            nome="Nome atualizado",
            email="PESSOA@EXAMPLE.COM",
            telefone="00000000000",
            endereco="Endereço atualizado",
        )

        self.assertEqual(self.usuario.nome, "Nome atualizado")
        self.assertEqual(
            self.usuario.email,
            "pessoa@example.com",
        )


if __name__ == "__main__":
    unittest.main()