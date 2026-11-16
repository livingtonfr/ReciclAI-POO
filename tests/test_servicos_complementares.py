import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.dao.material_dao import MaterialDAO
from app.dao.transacao_dao import TransacaoDAO
from app.model.comercial import Transacao
from app.model.enums import CategoriaMaterial, CondicaoMaterial
from app.model.material import TipoMaterial
from app.model.usuario import (
    UsuarioComum,
    Catador,
    EmpresaCompradora,
)
from app.services.identificacao_service import (
    IdentificacaoService,
    AcessoIdentificacaoNegadoError,
)
from app.services.rastreabilidade_service import (
    RastreabilidadeService,
)
from app.services.material_service import (
    AcessoMaterialNegadoError,
    MaterialNaoEncontradoError,
)
from app.services.demo_service import (
    DemoService,
    ResetDemoNegadoError,
)


class TestServicosComplementares(unittest.TestCase):

    def setUp(self):
        self.comum = UsuarioComum(
            "Pessoa", "pessoa@example.com", "hash",
            "000", "Endereço",
        )
        self.catador = Catador(
            "Catador", "catador@example.com", "hash",
            "000", "Endereço", "00000000000",
        )
        self.empresa = EmpresaCompradora(
            "Empresa", "empresa@example.com", "hash",
            "000", "Endereço", "00000000000000",
        )

        tipo = TipoMaterial(
            "PET",
            "PET para testes",
            CategoriaMaterial.PLASTICO,
        )
        self.material = self.catador.registrarMaterial(
            tipo,
            10.0,
            CondicaoMaterial.LIMPO,
        )

        self.repositorio = SimpleNamespace(
            materiais=[self.material],
            transacoes=[],
        )
        self.rastreabilidade = RastreabilidadeService(
            MaterialDAO(self.repositorio),
            TransacaoDAO(self.repositorio),
        )

    def test_identificacao_respeita_perfil(self):
        visao = Mock()
        servico = IdentificacaoService(visao)

        resultado = servico.identificar(
            self.comum,
            "foto.jpg",
        )

        self.assertIs(
            resultado,
            visao.identificarResiduo.return_value,
        )
        visao.identificarResiduo.assert_called_once_with(
            "foto.jpg"
        )

        visao.reset_mock()

        with self.assertRaises(AcessoIdentificacaoNegadoError):
            servico.identificar(self.catador, "foto.jpg")

        visao.identificarResiduo.assert_not_called()

    def test_historico_restrito_ao_responsavel_ou_participante(self):
        self.material.disponibilizar()
        lote = self.catador.criarLote(self.material)
        lote.disponibilizar()

        proposta = Transacao(
            lote,
            self.catador,
            self.empresa,
            20.0,
        )
        self.repositorio.transacoes.append(proposta)

        # Uma proposta pendente não dá acesso ao histórico.
        with self.assertRaises(AcessoMaterialNegadoError):
            self.rastreabilidade.consultar_historico(
                self.material.id,
                self.empresa,
            )

        proposta.concluir()

        for participante in (self.catador, self.empresa):
            historico = self.rastreabilidade.consultar_historico(
                self.material.id,
                participante,
            )
            self.assertEqual(
                historico,
                self.material.obterHistorico(),
            )

        with self.assertRaises(AcessoMaterialNegadoError):
            self.rastreabilidade.consultar_historico(
                self.material.id,
                self.comum,
            )

    def test_historico_recusa_anonimo_e_material_inexistente(self):
        with self.assertRaises(AcessoMaterialNegadoError):
            self.rastreabilidade.consultar_historico(
                self.material.id,
                None,
            )

        with self.assertRaises(MaterialNaoEncontradoError):
            self.rastreabilidade.consultar_historico(
                "id-inexistente",
                self.catador,
            )

    def test_reset_so_executa_quando_permitido(self):
        reinicializar = Mock()
        servico = DemoService(reinicializar)

        with self.assertRaises(ResetDemoNegadoError):
            servico.resetar(self.comum, False)

        with self.assertRaises(ResetDemoNegadoError):
            servico.resetar(None, True)

        reinicializar.assert_not_called()

        servico.resetar(self.comum, True)

        reinicializar.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()