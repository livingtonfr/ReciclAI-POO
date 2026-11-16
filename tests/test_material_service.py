import unittest
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


if __name__ == "__main__":
    unittest.main()