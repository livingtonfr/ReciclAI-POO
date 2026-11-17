import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock

from app.dao.material_dao import MaterialDAO
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
from app.model.servicos_ia import VisaoComputacionalIA
from app.model.usuario import Catador
from app.services.material_service import (
    MaterialService,
    AcessoMaterialNegadoError,
)


class TestMaterialServiceSQLite(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)

        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

        self.tipo = TipoMaterial(
            "PET",
            "Teste",
            CategoriaMaterial.PLASTICO,
        )
        self.usuario = Catador(
            "Teste",
            "teste@example.com",
            "hash",
            "000",
            "Rua",
            "00000000000",
        )
        self.material = Material(
            self.tipo,
            10,
            CondicaoMaterial.LIMPO,
            self.usuario,
        )

        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(self.tipo)
            UsuarioSQLiteDAO(conexao).adicionar(self.usuario)
            MaterialSQLiteDAO(conexao).adicionar(self.material)

    def recuperar(self):
        with conectar(self.caminho) as conexao:
            return MaterialSQLiteDAO(conexao).buscar_por_id(
                self.material.id
            )

    def test_disponibiliza_com_usuario_reconstruido(self):
        with conectar(self.caminho) as conexao:
            usuario = UsuarioSQLiteDAO(conexao).buscar_por_id(
                self.usuario.id
            )
            servico = MaterialService(
                MaterialSQLiteDAO(conexao)
            )

            material = servico.buscar_do_usuario(
                self.material.id,
                usuario,
            )

            self.assertIsNot(
                material.responsavelAtual,
                usuario,
            )

            servico.disponibilizar(material.id, usuario)

        self.assertIs(
            self.recuperar().status,
            StatusMaterial.DISPONIVEL,
        )

    def test_avaliacao_persiste_e_preserva_retorno(self):
        visao = VisaoComputacionalIA(
            self.tipo,
            0.8,
            CondicaoMaterial.SUJO,
            0.9,
        )

        with conectar(self.caminho) as conexao:
            servico = MaterialService(
                MaterialSQLiteDAO(conexao),
                servico_visao=visao,
            )
            avaliacao = servico.avaliar(
                self.material.id,
                self.usuario,
                "foto-teste",
            )

        recuperado = self.recuperar()

        self.assertEqual(
            [a.id for a in recuperado.obterAvaliacoes()],
            [avaliacao.id],
        )
        self.assertIs(
            recuperado.obterAvaliacoes()[0].condicaoDetectada,
            CondicaoMaterial.SUJO,
        )
        self.assertEqual(
            len(recuperado.obterHistorico()),
            1,
        )

    def test_outro_usuario_nao_pode_operar(self):
        outro = Catador(
            "Outro",
            "outro@example.com",
            "hash",
            "000",
            "Rua",
            "11111111111",
        )
        visao = Mock()

        with conectar(self.caminho) as conexao:
            servico = MaterialService(
                MaterialSQLiteDAO(conexao),
                servico_visao=visao,
            )

            with self.assertRaises(AcessoMaterialNegadoError):
                servico.disponibilizar(
                    self.material.id,
                    outro,
                )

            with self.assertRaises(AcessoMaterialNegadoError):
                servico.avaliar(
                    self.material.id,
                    outro,
                    "foto",
                )

            visao.avaliarMaterial.assert_not_called()

        self.assertIs(
            self.recuperar().status,
            StatusMaterial.REGISTRADO,
        )
        self.assertEqual(
            self.recuperar().obterAvaliacoes(),
            [],
        )

    def test_falha_posterior_reverte_operacoes_do_servico(self):
        visao = VisaoComputacionalIA(
            self.tipo,
            0.8,
            CondicaoMaterial.SUJO,
            0.9,
        )

        with self.assertRaises(RuntimeError):
            with conectar(self.caminho) as conexao:
                servico = MaterialService(
                    MaterialSQLiteDAO(conexao),
                    servico_visao=visao,
                )

                servico.disponibilizar(
                    self.material.id,
                    self.usuario,
                )
                servico.avaliar(
                    self.material.id,
                    self.usuario,
                    "foto",
                )

                raise RuntimeError("Falha posterior")

        recuperado = self.recuperar()

        self.assertIs(
            recuperado.status,
            StatusMaterial.REGISTRADO,
        )
        self.assertEqual(
            recuperado.obterAvaliacoes(),
            [],
        )

    def test_memoria_preserva_instancia_e_consulta_por_uuid(self):
        dao = MaterialDAO(
            SimpleNamespace(materiais=[self.material])
        )

        with conectar(self.caminho) as conexao:
            usuario = UsuarioSQLiteDAO(conexao).buscar_por_id(
                self.usuario.id
            )

        self.assertEqual(
            dao.listar_por_responsavel(usuario),
            [self.material],
        )

        resultado = MaterialService(dao).disponibilizar(
            self.material.id,
            usuario,
        )

        self.assertIs(resultado, self.material)
        self.assertIs(
            dao.buscar_por_id(self.material.id),
            self.material,
        )

    def test_memoria_recusa_instancia_externa_e_material_inexistente(self):
        dao = MaterialDAO(
            SimpleNamespace(materiais=[self.material])
        )

        with self.assertRaises(ValueError):
            dao.atualizar(self.recuperar())

        outro = Material(
            self.tipo,
            20,
            CondicaoMaterial.LIMPO,
            self.usuario,
        )

        with self.assertRaises(ValueError):
            dao.atualizar(outro)

        self.assertIs(
            dao.buscar_por_id(self.material.id),
            self.material,
        )


if __name__ == "__main__":
    unittest.main()