import unittest
from unittest.mock import Mock
from types import SimpleNamespace

from app.dao.material_dao import MaterialDAO
from app.model.enums import (
    CategoriaMaterial,
    CondicaoMaterial,
    StatusMaterial,
)
from app.model.material import TipoMaterial
from app.model.usuario import Catador, IndustriaTransformadora
from app.services.material_service import (
    MaterialService,
    AcessoMaterialNegadoError,
    MaterialNaoEncontradoError,
)
from app.model.servicos_ia import (
    VisaoComputacionalIA,
    PrecificacaoIA,
)


class TestMaterialService(unittest.TestCase):

    def setUp(self):
        # Armazenamento exclusivo de cada teste.
        self.repositorio = SimpleNamespace(materiais=[])
        self.dao = MaterialDAO(self.repositorio)
        self.servico = MaterialService(self.dao)

        self.catador = Catador(
            "Catador A",
            "a@example.com",
            "hash-teste",
            "00000000000",
            "Endereço A",
            "00000000000",
        )
        self.outro_catador = Catador(
            "Catador B",
            "b@example.com",
            "hash-teste",
            "00000000000",
            "Endereço B",
            "11111111111",
        )
        self.industria = IndustriaTransformadora(
            "Indústria",
            "industria@example.com",
            "hash-teste",
            "00000000000",
            "Endereço C",
            "00000000000000",
        )
        self.tipo = TipoMaterial(
            nome="PET",
            descricao="PET para testes",
            categoria=CategoriaMaterial.PLASTICO,
        )

    def registrar_material(self):
        return self.servico.registrar(
            self.catador,
            self.tipo,
            10.0,
            CondicaoMaterial.LIMPO,
        )

    def test_cadastro_armazena_uma_vez_e_permite_consulta(self):
        material = self.registrar_material()

        self.assertEqual(self.repositorio.materiais, [material])
        self.assertEqual(
            self.servico.listar_do_usuario(self.catador),
            [material],
        )
        self.assertEqual(
            self.servico.listar_do_usuario(self.outro_catador),
            [],
        )
        self.assertIs(
            self.servico.buscar_do_usuario(
                str(material.id),
                self.catador,
            ),
            material,
        )

        with self.assertRaises(ValueError):
            self.dao.adicionar(material)

        self.assertEqual(self.repositorio.materiais, [material])

    def test_peso_invalido_nao_armazena_material(self):
        with self.assertRaises(ValueError):
            self.servico.registrar(
                self.catador,
                self.tipo,
                50_001,
                CondicaoMaterial.LIMPO,
            )

        self.assertEqual(self.repositorio.materiais, [])

    def test_industria_nao_cadastra_material(self):
        with self.assertRaises(AcessoMaterialNegadoError):
            self.servico.registrar(
                self.industria,
                self.tipo,
                10.0,
                CondicaoMaterial.LIMPO,
            )

        self.assertEqual(self.repositorio.materiais, [])

    def test_disponibilizacao_respeita_responsavel_e_estado(self):
        material = self.registrar_material()

        with self.assertRaises(AcessoMaterialNegadoError):
            self.servico.disponibilizar(
                material.id,
                self.outro_catador,
            )

        self.assertEqual(
            material.status,
            StatusMaterial.REGISTRADO,
        )

        self.servico.disponibilizar(
            material.id,
            self.catador,
        )
        self.assertEqual(
            material.status,
            StatusMaterial.DISPONIVEL,
        )

        with self.assertRaises(ValueError):
            self.servico.disponibilizar(
                material.id,
                self.catador,
            )

        self.assertEqual(
            material.status,
            StatusMaterial.DISPONIVEL,
        )

    def test_busca_distingue_inexistencia_e_acesso_negado(self):
        material = self.registrar_material()

        with self.assertRaises(MaterialNaoEncontradoError):
            self.servico.buscar_do_usuario(
                "id-inexistente",
                self.catador,
            )

        with self.assertRaises(AcessoMaterialNegadoError):
            self.servico.buscar_do_usuario(
                material.id,
                self.outro_catador,
            )

    def configurar_servicos_ia(self):
        self.servico = MaterialService(
            material_dao=self.dao,
            servico_visao=VisaoComputacionalIA(
                tipoMaterialSimulado=self.tipo,
                confiancaIdentificacaoSimulada=0.8,
                condicaoSimulada=CondicaoMaterial.SUJO,
                confiancaAvaliacaoSimulada=0.9,
            ),
            servico_precificacao=PrecificacaoIA(2.75),
        )

    def test_avaliacao_preserva_condicao_declarada(self):
        self.configurar_servicos_ia()
        material = self.registrar_material()

        avaliacao = self.servico.avaliar(
            material.id,
            self.catador,
            "foto_teste.jpg",
        )

        self.assertEqual(
            material.condicaoDeclarada,
            CondicaoMaterial.LIMPO,
        )
        self.assertEqual(
            avaliacao.condicaoDetectada,
            CondicaoMaterial.SUJO,
        )
        self.assertEqual(
            material.obterAvaliacoes(),
            [avaliacao],
        )

    def test_cotacao_referencia_material_correto(self):
        self.configurar_servicos_ia()
        material = self.registrar_material()

        cotacao = self.servico.cotar(
            material.id,
            self.catador,
            15,
        )

        self.assertIs(cotacao.material, material)
        self.assertIsNone(cotacao.lote)
        self.assertEqual(cotacao.valorPorKg, 2.75)
        self.assertEqual(cotacao.horizonteDias, 15)

        with self.assertRaises(ValueError):
            self.servico.cotar(
                material.id,
                self.catador,
                0,
            )

    def test_outro_responsavel_nao_aciona_servicos_ia(self):
        material = self.registrar_material()
        visao = Mock()
        precificacao = Mock()

        servico = MaterialService(
            material_dao=self.dao,
            servico_visao=visao,
            servico_precificacao=precificacao,
        )

        with self.assertRaises(AcessoMaterialNegadoError):
            servico.avaliar(
                material.id,
                self.outro_catador,
                "foto_teste.jpg",
            )

        with self.assertRaises(AcessoMaterialNegadoError):
            servico.cotar(
                material.id,
                self.outro_catador,
                15,
            )

        visao.avaliarMaterial.assert_not_called()
        precificacao.cotarMaterial.assert_not_called()
        self.assertEqual(material.obterAvaliacoes(), [])

    def test_industria_nao_opera_mesmo_sendo_responsavel(self):
        material = self.registrar_material()

        # Prepara um material sob responsabilidade da indústria.
        material.transferirResponsabilidade(self.industria)

        visao = Mock()
        precificacao = Mock()

        servico = MaterialService(
            material_dao=self.dao,
            servico_visao=visao,
            servico_precificacao=precificacao,
        )

        with self.assertRaises(AcessoMaterialNegadoError):
            servico.avaliar(
                material.id,
                self.industria,
                "foto_teste.jpg",
            )

        with self.assertRaises(AcessoMaterialNegadoError):
            servico.cotar(
                material.id,
                self.industria,
                15,
            )

        visao.avaliarMaterial.assert_not_called()
        precificacao.cotarMaterial.assert_not_called()


if __name__ == "__main__":
    unittest.main()