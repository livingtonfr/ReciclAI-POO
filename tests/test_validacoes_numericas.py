import unittest

from app.model.enums import CategoriaMaterial, CondicaoMaterial
from app.model.usuario import Catador, EmpresaCompradora
from app.model.material import Material, TipoMaterial, AvaliacaoQualidade
from app.model.lote import LoteMaterial
from app.model.comercial import CotacaoPreco, Transacao
from app.model.servicos_ia import (
    ResultadoIdentificacao,
    VisaoComputacionalIA,
    PrecificacaoIA,
)


class TestValidacoesNumericas(unittest.TestCase):

    def setUp(self):
        self.tipo = TipoMaterial(
            "PET",
            "Material de teste",
            CategoriaMaterial.PLASTICO,
        )

        # Estas contas são usadas somente nos testes de domínio.
        # Não realizamos autenticação com elas.
        self.catador = Catador(
            "Catador Teste",
            "catador@example.test",
            "hash-nao-utilizado",
            "62900000000",
            "Endereco de teste",
            "12345678900",
        )

        self.empresa = EmpresaCompradora(
            "Empresa Teste",
            "empresa@example.test",
            "hash-nao-utilizado",
            "62900000001",
            "Endereco de teste",
            "12345678000199",
        )

    def criar_material(self, peso=10.0):
        return Material(
            self.tipo,
            peso,
            CondicaoMaterial.LIMPO,
            self.catador,
        )

    def criar_lote(self):
        material = self.criar_material()
        material.disponibilizar()
        return LoteMaterial(self.catador, material)

    def valores_positivos_invalidos(self):
        return (
            0,
            -1,
            float("nan"),
            float("inf"),
            float("-inf"),
            True,
            "10",
            None,
        )

    def test_material_recusa_pesos_invalidos(self):
        for peso in self.valores_positivos_invalidos():
            with self.subTest(peso=peso):
                with self.assertRaises(ValueError):
                    self.criar_material(peso)

    def test_material_aceita_peso_valido(self):
        material = self.criar_material(10.5)
        self.assertEqual(material.pesoKg, 10.5)

    def test_pesagem_invalida_preserva_valor_anterior(self):
        lote = self.criar_lote()
        lote.registrarPesagem(9.5)

        for peso in self.valores_positivos_invalidos():
            with self.subTest(peso=peso):
                with self.assertRaises(ValueError):
                    lote.registrarPesagem(peso)

                self.assertEqual(lote.pesoRegistrado, 9.5)

    def test_cotacao_recusa_precos_invalidos(self):
        material = self.criar_material()

        for preco in self.valores_positivos_invalidos():
            with self.subTest(preco=preco):
                with self.assertRaises(ValueError):
                    CotacaoPreco(preco, 15, material=material)

    def test_cotacao_recusa_prazos_invalidos(self):
        material = self.criar_material()

        for prazo in (0, -1, 1.5, float("nan"), float("inf"), True, "15", None):
            with self.subTest(prazo=prazo):
                with self.assertRaises(ValueError):
                    CotacaoPreco(2.75, prazo, material=material)

    def test_cotacao_valida(self):
        material = self.criar_material()
        cotacao = CotacaoPreco(2.75, 15, material=material)

        self.assertEqual(cotacao.valorPorKg, 2.75)
        self.assertEqual(cotacao.horizonteDias, 15)
        self.assertIs(cotacao.material, material)
        self.assertIsNone(cotacao.lote)

    def test_transacao_recusa_valores_sem_registrar_proposta(self):
        lote = self.criar_lote()
        lote.disponibilizar()

        for valor in self.valores_positivos_invalidos():
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    Transacao(lote, self.catador, self.empresa, valor)

                self.assertEqual(len(lote.transacoes), 0)

    def test_confiancas_invalidas(self):
        valores = (-0.1, 1.1, float("nan"), float("inf"), True, "0.8", None)

        for valor in valores:
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    AvaliacaoQualidade(CondicaoMaterial.LIMPO, valor)

                with self.assertRaises(ValueError):
                    ResultadoIdentificacao(self.tipo, valor)

                with self.assertRaises(ValueError):
                    VisaoComputacionalIA(
                        self.tipo, valor, CondicaoMaterial.SUJO, 0.9
                    )

                with self.assertRaises(ValueError):
                    VisaoComputacionalIA(
                        self.tipo, 0.8, CondicaoMaterial.SUJO, valor
                    )

    def test_confianca_aceita_limites(self):
        for valor in (0, 0.5, 1):
            with self.subTest(valor=valor):
                resultado = ResultadoIdentificacao(self.tipo, valor)
                avaliacao = AvaliacaoQualidade(CondicaoMaterial.LIMPO, valor)

                self.assertEqual(resultado.confianca, valor)
                self.assertEqual(avaliacao.confianca, valor)

    def test_precificacao_recusa_valor_base_invalido(self):
        for valor in self.valores_positivos_invalidos():
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    PrecificacaoIA(valor)

    def test_material_respeita_limite_de_peso(self):
        for peso in (0.5, 20_000, 50_000):
            with self.subTest(peso=peso):
                material = self.criar_material(peso)
                self.assertEqual(material.pesoKg, peso)

        for peso in (50_000.01, 1e107):
            with self.subTest(peso=peso):
                with self.assertRaises(ValueError):
                    self.criar_material(peso)

    def test_lote_aceita_soma_no_limite(self):
        primeiro = self.criar_material(30_000)
        segundo = self.criar_material(20_000)

        primeiro.disponibilizar()
        segundo.disponibilizar()

        lote = LoteMaterial(self.catador, primeiro)
        lote.adicionarMaterial(segundo)

        self.assertEqual(lote.calcularPesoTotal(), 50_000)
        self.assertEqual(len(lote.materiais), 2)
        self.assertIs(segundo.loteAtual, lote)

    def test_lote_recusa_excesso_sem_alterar_materiais(self):
        primeiro = self.criar_material(30_000)
        segundo = self.criar_material(25_000)

        primeiro.disponibilizar()
        segundo.disponibilizar()

        lote = LoteMaterial(self.catador, primeiro)
        status_anterior = segundo.status

        with self.assertRaises(ValueError):
            lote.adicionarMaterial(segundo)

        self.assertEqual(lote.calcularPesoTotal(), 30_000)
        self.assertEqual(len(lote.materiais), 1)
        self.assertNotIn(segundo, lote.materiais)
        self.assertIsNone(segundo.loteAtual)
        self.assertEqual(segundo.status, status_anterior)

    def test_pesagem_respeita_limite_sem_apagar_anterior(self):
        lote = self.criar_lote()
        lote.registrarPesagem(50_000)

        self.assertEqual(lote.pesoRegistrado, 50_000)

        for peso in (50_000.01, 1e107):
            with self.subTest(peso=peso):
                with self.assertRaises(ValueError):
                    lote.registrarPesagem(peso)

                self.assertEqual(lote.pesoRegistrado, 50_000)


if __name__ == "__main__":
    unittest.main()