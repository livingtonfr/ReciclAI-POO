import unittest

from app.model.enums import (
    CategoriaMaterial,
    CondicaoMaterial,
    StatusMaterial,
)
from app.model.material import Material, TipoMaterial
from app.model.lote import LoteMaterial
from app.model.usuario import (
    UsuarioComum,
    Catador,
    Cooperativa,
    EmpresaCompradora,
    IndustriaTransformadora,
)


class TestPermissoesLotes(unittest.TestCase):

    def setUp(self):
        self.tipo = TipoMaterial(
            nome="PET",
            descricao="Plástico PET para testes",
            categoria=CategoriaMaterial.PLASTICO,
        )

    def criar_usuario(self, classe):
        argumentos = [
            "Pessoa de teste",
            "teste@example.com",
            "hash-apenas-para-teste",
            "00000000000",
            "Endereço de teste",
        ]

        if classe is not UsuarioComum:
            argumentos.append("00000000000")

        return classe(*argumentos)

    def criar_material_disponivel(self, responsavel):
        material = Material(
            self.tipo,
            10.0,
            CondicaoMaterial.LIMPO,
            responsavel,
        )
        material.disponibilizar()
        return material

    def test_perfis_autorizados_criam_lote(self):
        for classe in (
            Catador,
            Cooperativa,
            EmpresaCompradora,
        ):
            with self.subTest(perfil=classe.__name__):
                usuario = self.criar_usuario(classe)
                material = self.criar_material_disponivel(usuario)

                lote = usuario.criarLote(material)

                self.assertIs(lote.criador, usuario)
                self.assertIn(material, lote.materiais)
                self.assertIs(material.loteAtual, lote)
                self.assertEqual(
                    material.status,
                    StatusMaterial.EM_LOTE,
                )

    def test_industria_nao_cria_lote_diretamente(self):
        industria = self.criar_usuario(
            IndustriaTransformadora
        )
        material = self.criar_material_disponivel(industria)

        with self.assertRaisesRegex(
            ValueError,
            "Somente catadores",
        ):
            LoteMaterial(industria, material)

        self.assertIsNone(material.loteAtual)
        self.assertEqual(
            material.status,
            StatusMaterial.DISPONIVEL,
        )

    def test_usuario_comum_nao_cria_lote_diretamente(self):
        usuario = self.criar_usuario(UsuarioComum)
        material = self.criar_material_disponivel(usuario)

        with self.assertRaisesRegex(
            ValueError,
            "Somente catadores",
        ):
            LoteMaterial(usuario, material)

        self.assertIsNone(material.loteAtual)
        self.assertEqual(
            material.status,
            StatusMaterial.DISPONIVEL,
        )

    def test_perfil_autorizado_nao_usa_material_de_outro(self):
        dono = self.criar_usuario(Catador)
        material = self.criar_material_disponivel(dono)

        for classe in (
            Catador,
            Cooperativa,
            EmpresaCompradora,
        ):
            with self.subTest(perfil=classe.__name__):
                outro_usuario = self.criar_usuario(classe)

                with self.assertRaises(ValueError):
                    LoteMaterial(outro_usuario, material)

                self.assertIs(material.responsavelAtual, dono)
                self.assertIsNone(material.loteAtual)
                self.assertEqual(
                    material.status,
                    StatusMaterial.DISPONIVEL,
                )


if __name__ == "__main__":
    unittest.main()