import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.model.usuario import Usuario, UsuarioComum
from app.services.usuario_service import UsuarioService


class TestPerfilSQLite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hash_senha = generate_password_hash("senha123")

    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)

        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

        self.usuario = Usuario.reconstituir(
            "empresa",
            str(uuid4()),
            "Original",
            "original@example.com",
            self.hash_senha,
            "000",
            "Rua antiga",
            "2020-01-01T12:00:00",
            latitude=-16.68,
            longitude=-49.25,
            cnpj="00000000000000",
            statusValidacao="APROVADA",
        )

        with conectar(self.caminho) as conexao:
            UsuarioSQLiteDAO(conexao).adicionar(self.usuario)

    def atualizar(self, conexao, **alteracoes):
        dados = dict(
            nome=" Novo nome ",
            email=" NOVO@EXAMPLE.COM ",
            telefone=" 111 ",
            endereco=" Rua nova ",
        )
        dados.update(alteracoes)

        return UsuarioService(
            UsuarioSQLiteDAO(conexao)
        ).atualizar_perfil(
            self.usuario,
            **dados,
        )

    def conferir_original(self):
        with conectar(self.caminho) as conexao:
            salvo = UsuarioSQLiteDAO(
                conexao
            ).buscar_por_id(self.usuario.id)

        for campo in (
            "nome", "email", "telefone",
            "endereco", "latitude", "longitude",
        ):
            self.assertEqual(
                getattr(salvo, campo),
                getattr(self.usuario, campo),
            )

    def test_atualiza_objeto_reconstruido_e_persiste(self):
        with conectar(self.caminho) as conexao:
            atualizado = self.atualizar(conexao)
            self.assertEqual(atualizado.id, self.usuario.id)

        with conectar(self.caminho) as conexao:
            salvo = UsuarioService(
                UsuarioSQLiteDAO(conexao)
            ).autenticar(
                "novo@example.com",
                "senha123",
            )

        self.assertEqual(salvo.nome, "Novo nome")
        self.assertEqual(salvo.email, "novo@example.com")
        self.assertEqual(salvo.telefone, "111")
        self.assertEqual(salvo.endereco, "Rua nova")
        self.assertIsNone(salvo.latitude)
        self.assertIsNone(salvo.longitude)

        for campo in (
            "id", "senhaHash", "criadoEm",
            "cnpj", "statusValidacao",
        ):
            self.assertEqual(
                getattr(salvo, campo),
                getattr(self.usuario, campo),
            )

        self.assertIs(type(salvo), type(self.usuario))

    def test_permite_manter_proprio_email(self):
        with conectar(self.caminho) as conexao:
            self.atualizar(
                conexao,
                email=" ORIGINAL@EXAMPLE.COM ",
            )

        with conectar(self.caminho) as conexao:
            salvo = UsuarioSQLiteDAO(
                conexao
            ).buscar_por_id(self.usuario.id)

            self.assertEqual(
                salvo.email, "original@example.com"
            )
            self.assertEqual(salvo.nome, "Novo nome")

    def test_duplicidade_preserva_banco_e_objeto_recebido(self):
        with conectar(self.caminho) as conexao:
            UsuarioSQLiteDAO(conexao).adicionar(
                UsuarioComum(
                    "Outra",
                    "outra@example.com",
                    self.hash_senha,
                    "222",
                    "Outra rua",
                )
            )

        with self.assertRaisesRegex(ValueError, "e-mail"):
            with conectar(self.caminho) as conexao:
                self.atualizar(
                    conexao,
                    email=" OUTRA@EXAMPLE.COM ",
                )

        self.assertEqual(self.usuario.nome, "Original")
        self.assertEqual(
            self.usuario.email, "original@example.com"
        )
        self.conferir_original()

    def test_dados_invalidos_e_usuario_ausente_nao_gravam(self):
        for alteracao in (
            {"nome": " "},
            {"email": "sem-arroba"},
        ):
            with self.subTest(alteracao=alteracao):
                with self.assertRaises(ValueError):
                    with conectar(self.caminho) as conexao:
                        self.atualizar(conexao, **alteracao)

        ausente = UsuarioComum(
            "Ausente",
            "ausente@example.com",
            self.hash_senha,
            "0",
            "Rua",
        )

        for usuario in (None, ausente):
            with self.subTest(usuario=usuario):
                with self.assertRaisesRegex(
                    ValueError, "não encontrado"
                ):
                    with conectar(self.caminho) as conexao:
                        UsuarioService(
                            UsuarioSQLiteDAO(conexao)
                        ).atualizar_perfil(
                            usuario,
                            "Nome",
                            "novo@example.com",
                            "111",
                            "Rua",
                        )

        self.conferir_original()

    def test_erro_posterior_reverte_atualizacao(self):
        with self.assertRaisesRegex(
            RuntimeError, "Falha posterior"
        ):
            with conectar(self.caminho) as conexao:
                self.atualizar(conexao)
                raise RuntimeError("Falha posterior")

        self.conferir_original()


if __name__ == "__main__":
    unittest.main()