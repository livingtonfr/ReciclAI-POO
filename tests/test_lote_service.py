import unittest
from types import SimpleNamespace

from app.dao.lote_dao import LoteDAO
from app.dao.material_dao import MaterialDAO
from app.model.enums import CategoriaMaterial, CondicaoMaterial
from app.model.material import TipoMaterial
from app.model.usuario import Catador, IndustriaTransformadora
from app.services.lote_service import LoteService, LoteNaoEncontradoError, AcessoLoteNegadoError


class TestLoteService(unittest.TestCase):

    def setUp(self):
        self.repositorio = SimpleNamespace(
            materiais=[],
            lotes=[],
        )
        self.servico = LoteService(
            LoteDAO(self.repositorio),
            MaterialDAO(self.repositorio),
        )

        self.catador = self.criar_catador("A")
        self.outro_catador = self.criar_catador("B")

        self.tipo = TipoMaterial(
            nome="PET",
            descricao="PET para testes",
            categoria=CategoriaMaterial.PLASTICO,
        )

        material = self.criar_material(
            self.catador,
            disponivel=True,
        )
        self.lote = self.catador.criarLote(material)
        self.repositorio.lotes.append(self.lote)

    def criar_catador(self, nome):
        return Catador(
            nome,
            nome.lower() + "@example.com",
            "hash-teste",
            "00000000000",
            "Endereço de teste",
            "00000000000",
        )

    def criar_material(self, usuario, disponivel=False):
        material = usuario.registrarMaterial(
            self.tipo,
            10.0,
            CondicaoMaterial.LIMPO,
        )

        if disponivel:
            material.disponibilizar()

        self.repositorio.materiais.append(material)
        return material

    def test_listagem_e_busca_do_criador(self):
        self.assertEqual(
            self.servico.listar_do_usuario(self.catador),
            [self.lote],
        )
        self.assertEqual(
            self.servico.listar_do_usuario(self.outro_catador),
            [],
        )
        self.assertIs(
            self.servico.buscar_do_usuario(
                str(self.lote.id),
                self.catador,
            ),
            self.lote,
        )

    def test_busca_distingue_inexistencia_e_acesso_negado(self):
        with self.assertRaises(LoteNaoEncontradoError):
            self.servico.buscar_do_usuario(
                "id-inexistente",
                self.catador,
            )

        with self.assertRaises(AcessoLoteNegadoError):
            self.servico.buscar_do_usuario(
                self.lote.id,
                self.outro_catador,
            )

    def test_filtra_materiais_por_responsavel_e_estado(self):
        disponivel = self.criar_material(
            self.catador,
            disponivel=True,
        )

        # Não devem aparecer: registrado, de outro usuário
        # ou já agrupado no lote criado no setUp.
        self.criar_material(self.catador)
        self.criar_material(
            self.outro_catador,
            disponivel=True,
        )

        self.assertEqual(
            self.servico.listar_materiais_disponiveis(
                self.catador
            ),
            [disponivel],
        )

        self.assertEqual(
            self.servico.listar_materiais_disponiveis(
                self.catador,
                excluir=disponivel,
            ),
            [],
        )

    def test_industria_nao_acessa_gerenciamento_de_lotes(self):
        industria = IndustriaTransformadora(
            "Indústria",
            "industria@example.com",
            "hash-teste",
            "00000000000",
            "Endereço de teste",
            "00000000000000",
        )

        with self.assertRaises(AcessoLoteNegadoError):
            self.servico.listar_do_usuario(industria)

        with self.assertRaises(AcessoLoteNegadoError):
            self.servico.buscar_do_usuario(
                self.lote.id,
                industria,
            )

        with self.assertRaises(AcessoLoteNegadoError):
            self.servico.listar_materiais_disponiveis(
                industria
            )


if __name__ == "__main__":
    unittest.main()