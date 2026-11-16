import unittest
from types import SimpleNamespace

from app.dao.lote_dao import LoteDAO
from app.dao.transacao_dao import TransacaoDAO
from app.model.comercial import Transacao
from app.model.enums import CategoriaMaterial, CondicaoMaterial
from app.model.material import Material, TipoMaterial
from app.model.servicos_ia import PrecificacaoIA
from app.model.usuario import Catador, EmpresaCompradora
from app.services.transacao_service import (
    TransacaoService,
    TransacaoNaoEncontradaError,
    AcessoTransacaoNegadoError,
)


class TestTransacaoService(unittest.TestCase):

    def setUp(self):
        self.repositorio = SimpleNamespace(
            lotes=[],
            transacoes=[],
        )

        self.catador = Catador(
            "Catador",
            "catador@example.com",
            "hash-teste",
            "00000000000",
            "Endereço de teste",
            "00000000000",
        )

        self.empresa = self.criar_empresa("Empresa A")
        self.outra_empresa = self.criar_empresa("Empresa B")

        self.tipo = TipoMaterial(
            nome="PET",
            descricao="PET para testes",
            categoria=CategoriaMaterial.PLASTICO,
        )

        self.servico = TransacaoService(
            TransacaoDAO(self.repositorio),
            LoteDAO(self.repositorio),
            PrecificacaoIA(2.0),
        )

    def criar_empresa(self, nome):
        return EmpresaCompradora(
            nome,
            nome.replace(" ", "").lower() + "@example.com",
            "hash-teste",
            "00000000000",
            "Endereço de teste",
            "00000000000000",
        )

    def criar_lote(self, criador, disponivel=True):
        material = Material(
            self.tipo,
            10.0,
            CondicaoMaterial.LIMPO,
            criador,
        )
        material.disponibilizar()
        lote = criador.criarLote(material)

        if disponivel:
            lote.disponibilizar()

        self.repositorio.lotes.append(lote)
        return lote

    def test_mercado_filtra_lotes_e_utiliza_pesagem(self):
        oferta = self.criar_lote(self.catador)
        oferta.registrarPesagem(8.0)

        self.criar_lote(self.empresa)
        self.criar_lote(self.catador, disponivel=False)

        cancelado = self.criar_lote(self.catador)
        cancelado.cancelar()

        ofertas = self.servico.listar_mercado(self.empresa)

        self.assertEqual(len(ofertas), 1)
        self.assertIs(ofertas[0]["lote"], oferta)
        self.assertEqual(ofertas[0]["peso"], 8.0)
        self.assertEqual(ofertas[0]["valor_sugerido"], 16.0)

    def test_mercado_utiliza_soma_quando_nao_ha_pesagem(self):
        lote = self.criar_lote(self.catador)

        ofertas = self.servico.listar_mercado(self.empresa)

        self.assertIs(ofertas[0]["lote"], lote)
        self.assertEqual(ofertas[0]["peso"], 10.0)
        self.assertEqual(ofertas[0]["valor_sugerido"], 20.0)

    def test_listas_separam_comprador_e_vendedor(self):
        lote = self.criar_lote(self.catador)
        proposta = Transacao(
            lote,
            self.catador,
            self.empresa,
            20.0,
        )
        self.repositorio.transacoes.append(proposta)

        self.assertEqual(
            self.servico.listar_propostas(self.empresa),
            [proposta],
        )
        self.assertEqual(
            self.servico.listar_propostas(self.outra_empresa),
            [],
        )
        self.assertEqual(
            self.servico.listar_vendas(self.catador),
            [proposta],
        )
        self.assertEqual(
            self.servico.listar_vendas(self.empresa),
            [],
        )

    def test_busca_confere_vendedor_e_existencia(self):
        lote = self.criar_lote(self.catador)
        proposta = Transacao(
            lote,
            self.catador,
            self.empresa,
            20.0,
        )
        self.repositorio.transacoes.append(proposta)

        self.assertIs(
            self.servico.buscar_do_vendedor(
                str(proposta.id),
                self.catador,
            ),
            proposta,
        )

        with self.assertRaises(AcessoTransacaoNegadoError):
            self.servico.buscar_do_vendedor(
                proposta.id,
                self.outra_empresa,
            )

        with self.assertRaises(TransacaoNaoEncontradaError):
            self.servico.buscar_do_vendedor(
                "id-inexistente",
                self.catador,
            )

    def test_catador_nao_acessa_operacoes_de_comprador(self):
        with self.assertRaises(AcessoTransacaoNegadoError):
            self.servico.listar_mercado(self.catador)

        with self.assertRaises(AcessoTransacaoNegadoError):
            self.servico.listar_propostas(self.catador)


if __name__ == "__main__":
    unittest.main()