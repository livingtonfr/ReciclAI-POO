import unittest
from uuid import uuid4

from app.model.comercial import Certificado, Transacao
from app.model.enums import (
    CategoriaMaterial,
    CondicaoMaterial,
    StatusLote,
    StatusTransacao,
)
from app.model.lote import LoteMaterial
from app.model.material import Material, TipoMaterial
from app.model.usuario import Catador, EmpresaCompradora


class TestComercialReconstituicao(unittest.TestCase):
    def setUp(self):
        self.vendedor = Catador(
            "Vendedor",
            "vendedor@example.com",
            "hash",
            "000",
            "Rua",
            "00000000000",
        )
        self.comprador = EmpresaCompradora(
            "Comprador",
            "comprador@example.com",
            "hash",
            "000",
            "Rua",
            "11111111111111",
        )

        tipo = TipoMaterial(
            "PET",
            "Teste",
            CategoriaMaterial.PLASTICO,
        )

        self.material = Material(
            tipo,
            10,
            CondicaoMaterial.LIMPO,
            self.vendedor,
        )
        self.material.disponibilizar()

        self.lote = self.vendedor.criarLote(self.material)
        self.lote.disponibilizar()

        self.data = "2026-11-16T12:00:00"

    def recuperar(self, lote=None, **alteracoes):
        if lote is None:
            lote = self.lote

        dados = {
            "identificador": str(uuid4()),
            "lote": lote,
            "vendedor": lote.criador,
            "comprador": self.comprador,
            "valorTotal": 100,
            "dataTransacao": self.data,
            "status": "PENDENTE",
        }
        dados.update(alteracoes)

        return Transacao.reconstituir(**dados)

    def test_certificado_preserva_identidade_e_data(self):
        identificador = uuid4()

        certificado = Certificado.reconstituir(
            str(identificador),
            "CERT-001",
            self.data,
        )

        self.assertEqual(certificado.id, identificador)
        self.assertEqual(certificado.codigo, "CERT-001")
        self.assertEqual(
            certificado.dataEmissao.isoformat(),
            self.data,
        )

        for codigo in ("", "   ", None):
            with self.subTest(codigo=codigo):
                with self.assertRaises(ValueError):
                    Certificado.reconstituir(
                        str(uuid4()),
                        codigo,
                        self.data,
                    )

    def test_pendente_nao_registra_eventos_ou_proposta_automaticamente(self):
        identificador = uuid4()
        eventos = [e.id for e in self.material.obterHistorico()]

        transacao = self.recuperar(
            identificador=str(identificador)
        )

        self.assertEqual(transacao.id, identificador)
        self.assertEqual(
            transacao.dataTransacao.isoformat(),
            self.data,
        )
        self.assertIs(
            transacao.status,
            StatusTransacao.PENDENTE,
        )
        self.assertEqual(self.lote.transacoes, [])
        self.assertIs(self.material.loteAtual, self.lote)
        self.assertIs(
            self.material.responsavelAtual,
            self.vendedor,
        )
        self.assertEqual(
            [e.id for e in self.material.obterHistorico()],
            eventos,
        )

        self.lote.restaurar_transacoes([transacao])

        self.assertIs(self.lote.transacoes[0], transacao)
        self.assertIs(transacao.lote, self.lote)

    def test_concluida_preserva_material_ja_reagrupado(self):
        original = Transacao(
            self.lote,
            self.vendedor,
            self.comprador,
            100,
        )
        original.concluir()

        novo = self.comprador.criarLote(self.material)
        eventos = [e.id for e in self.material.obterHistorico()]

        antigo = LoteMaterial.reconstituir_encerrado(
            identificador=self.lote.id,
            criador=self.vendedor,
            dataCriacao=self.lote.dataCriacao.isoformat(),
            status="NEGOCIADO",
            materiais=[self.material],
            pesoRegistrado=self.lote.pesoRegistrado,
        )

        certificado = Certificado.reconstituir(
            str(uuid4()),
            "CERT-002",
            self.data,
        )

        recuperada = self.recuperar(
            lote=antigo,
            identificador=original.id,
            dataTransacao=original.dataTransacao.isoformat(),
            status="CONCLUIDA",
            pesoNegociado=original.pesoNegociado,
            certificado=certificado,
        )
        antigo.restaurar_transacoes([recuperada])

        self.assertIs(antigo.status, StatusLote.NEGOCIADO)
        self.assertTrue(antigo.possuiTransacaoConcluida())
        self.assertIs(antigo.transacoes[0], recuperada)
        self.assertIs(recuperada.certificado, certificado)
        self.assertEqual(recuperada.pesoNegociado, 10)

        self.assertIs(self.material.loteAtual, novo)
        self.assertIs(
            self.material.responsavelAtual,
            self.comprador,
        )
        self.assertEqual(
            [e.id for e in self.material.obterHistorico()],
            eventos,
        )

    def test_cancelada_em_lote_cancelado(self):
        self.lote.cancelar()

        transacao = self.recuperar(status="CANCELADA")
        self.lote.restaurar_transacoes([transacao])

        self.assertIs(
            transacao.status,
            StatusTransacao.CANCELADA,
        )
        self.assertIsNone(transacao.pesoNegociado)
        self.assertIsNone(self.material.loteAtual)

    def test_recusa_dados_incompativeis_sem_alterar_lote(self):
        certificado = Certificado.reconstituir(
            str(uuid4()),
            "CERT-003",
            self.data,
        )

        invalidos = (
            {"valorTotal": True},
            {"valorTotal": float("inf")},
            {"valorTotal": 0},
            {"pesoNegociado": 10},
            {"status": "INVALIDO"},
            {"status": "CONCLUIDA", "pesoNegociado": 10},
            {"certificado": certificado},
            {"comprador": self.vendedor},
            {"vendedor": self.comprador},
        )

        for dados in invalidos:
            with self.subTest(dados=dados):
                with self.assertRaises(ValueError):
                    self.recuperar(**dados)

                self.assertEqual(self.lote.transacoes, [])
                self.assertIs(
                    self.material.loteAtual,
                    self.lote,
                )

    def test_restauracao_da_lista_e_atomica(self):
        primeira = self.recuperar()
        repetida = self.recuperar(
            identificador=primeira.id
        )

        with self.assertRaises(ValueError):
            self.lote.restaurar_transacoes(
                [primeira, repetida]
            )

        self.assertEqual(self.lote.transacoes, [])

        with self.assertRaises(ValueError):
            self.lote.restaurar_transacoes(
                [primeira, object()]
            )

        self.assertEqual(self.lote.transacoes, [])

        self.lote.restaurar_transacoes([primeira])

        with self.assertRaises(ValueError):
            self.lote.restaurar_transacoes([])

        self.assertIs(self.lote.transacoes[0], primeira)


if __name__ == "__main__":
    unittest.main()