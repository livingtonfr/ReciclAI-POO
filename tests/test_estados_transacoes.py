import unittest

from app.model.comercial import Transacao
from app.model.enums import (
    CategoriaMaterial,
    CondicaoMaterial,
    StatusLote,
    StatusMaterial,
    StatusTransacao,
)
from app.model.material import TipoMaterial
from app.model.usuario import Catador, EmpresaCompradora


class TestEstadosTransacoes(unittest.TestCase):

    def setUp(self):
        self.tipo = TipoMaterial(
            nome="PET",
            descricao="Plástico PET para testes",
            categoria=CategoriaMaterial.PLASTICO,
        )

        self.catador = Catador(
            nome="Catador de teste",
            email="catador@example.com",
            senhaHash="hash-de-teste",
            telefone="00000000000",
            endereco="Endereço de teste",
            cpf="00000000000",
        )

        self.empresa = self.criar_empresa("Empresa A")
        self.outra_empresa = self.criar_empresa("Empresa B")

        self.material = self.criar_material()
        self.segundo_material = self.criar_material()

        self.lote = self.catador.criarLote(self.material)
        self.lote.adicionarMaterial(self.segundo_material)
        self.lote.disponibilizar()

    def criar_empresa(self, nome):
        return EmpresaCompradora(
            nome=nome,
            email=nome.replace(" ", "").lower() + "@example.com",
            senhaHash="hash-de-teste",
            telefone="00000000000",
            endereco="Endereço de teste",
            cnpj="00000000000000",
        )

    def criar_material(self):
        material = self.catador.registrarMaterial(
            self.tipo,
            10.0,
            CondicaoMaterial.LIMPO,
        )
        material.disponibilizar()
        return material

    def criar_proposta(self, comprador):
        return Transacao(
            self.lote,
            self.catador,
            comprador,
            50.0,
        )

    def test_cancelar_lote_libera_materiais_e_cancela_proposta(self):
        proposta = self.criar_proposta(self.empresa)

        self.lote.cancelar()

        self.assertEqual(
            self.lote.status,
            StatusLote.CANCELADO,
        )
        self.assertEqual(
            proposta.status,
            StatusTransacao.CANCELADA,
        )

        for material in (self.material, self.segundo_material):
            self.assertIsNone(material.loteAtual)
            self.assertIs(
                material.responsavelAtual,
                self.catador,
            )
            self.assertEqual(
                material.status,
                StatusMaterial.DISPONIVEL,
            )

        with self.assertRaises(ValueError):
            proposta.concluir()

        self.assertIsNone(proposta.pesoNegociado)

    def test_concluir_cancela_concorrente_e_impede_repeticao(self):
        proposta = self.criar_proposta(self.empresa)
        concorrente = self.criar_proposta(self.outra_empresa)

        proposta.concluir()

        self.assertEqual(
            proposta.status,
            StatusTransacao.CONCLUIDA,
        )
        self.assertEqual(
            concorrente.status,
            StatusTransacao.CANCELADA,
        )
        self.assertEqual(
            self.lote.status,
            StatusLote.NEGOCIADO,
        )
        self.assertEqual(proposta.pesoNegociado, 20.0)

        historico_anterior = self.material.obterHistorico()

        with self.assertRaises(ValueError):
            proposta.concluir()

        with self.assertRaises(ValueError):
            self.lote.cancelar()

        with self.assertRaises(ValueError):
            concorrente.concluir()

        self.assertEqual(
            self.material.obterHistorico(),
            historico_anterior,
        )

        for material in (self.material, self.segundo_material):
            self.assertIs(material.responsavelAtual, self.empresa)
            self.assertIsNone(material.loteAtual)
            self.assertEqual(
                material.status,
                StatusMaterial.DISPONIVEL,
            )

    def test_mudanca_de_responsavel_impede_venda_parcial(self):
        proposta = self.criar_proposta(self.empresa)

        # Simula uma mudança depois da criação da proposta.
        self.segundo_material.transferirResponsabilidade(
            self.outra_empresa
        )
        historico_anterior = self.material.obterHistorico()

        with self.assertRaisesRegex(
            ValueError,
            "responsabilidade do vendedor",
        ):
            proposta.concluir()

        self.assertEqual(
            proposta.status,
            StatusTransacao.PENDENTE,
        )
        self.assertIsNone(proposta.pesoNegociado)
        self.assertEqual(
            self.lote.status,
            StatusLote.DISPONIVEL,
        )
        self.assertIs(
            self.material.responsavelAtual,
            self.catador,
        )
        self.assertIs(
            self.segundo_material.responsavelAtual,
            self.outra_empresa,
        )
        self.assertEqual(
            self.material.obterHistorico(),
            historico_anterior,
        )

    def test_vinculo_inconsistente_impede_venda_parcial(self):
        proposta = self.criar_proposta(self.empresa)

        # Simula uma inconsistência para testar a proteção.
        self.segundo_material.removerDoLote(self.lote)
        historico_anterior = self.material.obterHistorico()

        with self.assertRaisesRegex(
            ValueError,
            "vinculados ao lote",
        ):
            proposta.concluir()

        self.assertEqual(
            proposta.status,
            StatusTransacao.PENDENTE,
        )
        self.assertIsNone(proposta.pesoNegociado)
        self.assertEqual(
            self.lote.status,
            StatusLote.DISPONIVEL,
        )
        self.assertIs(
            self.material.responsavelAtual,
            self.catador,
        )
        self.assertIs(
            self.material.loteAtual,
            self.lote,
        )
        self.assertEqual(
            self.material.obterHistorico(),
            historico_anterior,
        )


if __name__ == "__main__":
    unittest.main()