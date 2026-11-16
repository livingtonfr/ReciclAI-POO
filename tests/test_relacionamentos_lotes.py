import unittest
from unittest.mock import patch

from app.model.enums import (
    CategoriaMaterial,
    CondicaoMaterial,
    StatusMaterial,
)
from app.model.material import Material, TipoMaterial
from app.model.usuario import Catador


class TestRelacionamentosLotes(unittest.TestCase):

    def setUp(self):
        self.tipo = TipoMaterial(
            nome="PET",
            descricao="Plástico PET para testes",
            categoria=CategoriaMaterial.PLASTICO,
        )

        self.catador = Catador(
            nome="Catador de teste",
            email="teste@example.com",
            senhaHash="hash-apenas-para-teste",
            telefone="00000000000",
            endereco="Endereço de teste",
            cpf="00000000000",
        )

    def criar_material_disponivel(self):
        material = Material(
            self.tipo,
            10.0,
            CondicaoMaterial.LIMPO,
            self.catador,
        )
        material.disponibilizar()
        return material

    def test_inclusao_e_remocao_atualizam_os_dois_lados(self):
        primeiro = self.criar_material_disponivel()
        segundo = self.criar_material_disponivel()
        lote = self.catador.criarLote(primeiro)

        lote.adicionarMaterial(segundo)

        self.assertIn(segundo, lote.materiais)
        self.assertIs(segundo.loteAtual, lote)
        self.assertEqual(
            segundo.status,
            StatusMaterial.EM_LOTE,
        )

        lote.removerMaterial(segundo)

        self.assertNotIn(segundo, lote.materiais)
        self.assertIsNone(segundo.loteAtual)
        self.assertEqual(
            segundo.status,
            StatusMaterial.DISPONIVEL,
        )
        self.assertEqual(lote.materiais, [primeiro])

    def test_material_nao_pode_entrar_em_dois_lotes(self):
        primeiro = self.criar_material_disponivel()
        segundo = self.criar_material_disponivel()

        lote_a = self.catador.criarLote(primeiro)
        lote_b = self.catador.criarLote(segundo)
        historico_anterior = primeiro.obterHistorico()

        with self.assertRaises(ValueError):
            lote_b.adicionarMaterial(primeiro)

        self.assertEqual(lote_a.materiais, [primeiro])
        self.assertEqual(lote_b.materiais, [segundo])
        self.assertIs(primeiro.loteAtual, lote_a)
        self.assertEqual(
            primeiro.obterHistorico(),
            historico_anterior,
        )

    def test_nao_remove_unico_material_do_lote(self):
        material = self.criar_material_disponivel()
        lote = self.catador.criarLote(material)

        with self.assertRaises(ValueError):
            lote.removerMaterial(material)

        self.assertEqual(lote.materiais, [material])
        self.assertIs(material.loteAtual, lote)
        self.assertEqual(
            material.status,
            StatusMaterial.EM_LOTE,
        )

    def test_recusa_do_agrupamento_preserva_lista(self):
        primeiro = self.criar_material_disponivel()
        segundo = self.criar_material_disponivel()
        lote = self.catador.criarLote(primeiro)
        historico_anterior = segundo.obterHistorico()

        with patch.object(
            Material,
            "agruparEmLote",
            side_effect=ValueError("Recusa simulada"),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Recusa simulada",
            ):
                lote.adicionarMaterial(segundo)

        self.assertEqual(lote.materiais, [primeiro])
        self.assertIsNone(segundo.loteAtual)
        self.assertEqual(
            segundo.status,
            StatusMaterial.DISPONIVEL,
        )
        self.assertEqual(
            segundo.obterHistorico(),
            historico_anterior,
        )

    def test_recusa_da_remocao_preserva_lista(self):
        primeiro = self.criar_material_disponivel()
        segundo = self.criar_material_disponivel()
        lote = self.catador.criarLote(primeiro)
        lote.adicionarMaterial(segundo)

        with patch.object(
            Material,
            "removerDoLote",
            side_effect=ValueError("Recusa simulada"),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Recusa simulada",
            ):
                lote.removerMaterial(segundo)

        self.assertEqual(
            lote.materiais,
            [primeiro, segundo],
        )
        self.assertIs(segundo.loteAtual, lote)
        self.assertEqual(
            segundo.status,
            StatusMaterial.EM_LOTE,
        )


if __name__ == "__main__":
    unittest.main()