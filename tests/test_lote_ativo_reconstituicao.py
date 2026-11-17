import unittest
from uuid import uuid4

from app.model.enums import (
    CategoriaMaterial,
    CondicaoMaterial,
    StatusMaterial,
)
from app.model.lote import LoteMaterial
from app.model.material import Material, TipoMaterial
from app.model.usuario import Catador


class TestLoteAtivoReconstituicao(unittest.TestCase):
    def setUp(self):
        self.usuario = Catador(
            "Teste",
            "teste@example.com",
            "hash",
            "000",
            "Rua",
            "00000000000",
        )
        self.tipo = TipoMaterial(
            "PET",
            "Teste",
            CategoriaMaterial.PLASTICO,
        )
        self.original = Material(
            self.tipo,
            10,
            CondicaoMaterial.LIMPO,
            self.usuario,
        )
        self.original.disponibilizar()

        self.lote_original = self.usuario.criarLote(
            self.original
        )

        self.dados = dict(
            identificador=str(self.original.id),
            tipoMaterial=self.tipo,
            pesoKg=10,
            condicaoDeclarada="LIMPO",
            responsavelAtual=self.usuario,
            status="EM_LOTE",
            dataRegistro=self.original.dataRegistro.isoformat(),
            eventos=self.original.obterHistorico(),
            avaliacoes=[],
        )

        self.lote_dados = dict(
            identificador=str(self.lote_original.id),
            criador=self.usuario,
            dataCriacao=self.lote_original.dataCriacao.isoformat(),
            status="EM_FORMACAO",
            dadosMateriais=[self.dados],
            pesoRegistrado=10,
        )

    def test_restaura_vinculos_sem_eventos_novos(self):
        lote = LoteMaterial.reconstituir_ativo(
            **self.lote_dados
        )
        material = lote.materiais[0]

        self.assertIs(material.loteAtual, lote)
        self.assertIs(material.status, StatusMaterial.EM_LOTE)
        self.assertIs(
            material.responsavelAtual,
            lote.criador,
        )
        self.assertEqual(material.id, self.original.id)
        self.assertEqual(lote.id, self.lote_original.id)
        self.assertEqual(
            lote.dataCriacao,
            self.lote_original.dataCriacao,
        )
        self.assertEqual(lote.pesoRegistrado, 10)
        self.assertEqual(
            material.obterHistorico(),
            self.original.obterHistorico(),
        )
        self.assertIs(
            self.original.loteAtual,
            self.lote_original,
        )

    def test_remocao_restaurada_invalida_pesagem(self):
        outro = self.dados | {
            "identificador": str(uuid4()),
            "eventos": [],
        }

        lote = LoteMaterial.reconstituir_ativo(
            **(
                self.lote_dados
                | {"dadosMateriais": [self.dados, outro]}
            )
        )
        material = lote.materiais[1]

        lote.removerMaterial(material)

        self.assertIsNone(material.loteAtual)
        self.assertIs(
            material.status,
            StatusMaterial.DISPONIVEL,
        )
        self.assertIsNone(lote.pesoRegistrado)

    def test_recusa_remocao_do_unico_preserva_pesagem(self):
        lote = LoteMaterial.reconstituir_ativo(
            **self.lote_dados
        )

        with self.assertRaises(ValueError):
            lote.removerMaterial(lote.materiais[0])

        self.assertEqual(lote.pesoRegistrado, 10)
        self.assertIs(
            lote.materiais[0].loteAtual,
            lote,
        )

    def test_lote_disponivel_preserva_restricoes(self):
        lote = LoteMaterial.reconstituir_ativo(
            **(
                self.lote_dados
                | {"status": "DISPONIVEL"}
            )
        )

        with self.assertRaises(ValueError):
            lote.removerMaterial(lote.materiais[0])

        lote.cancelar()

        self.assertIsNone(lote.materiais[0].loteAtual)
        self.assertIs(
            lote.materiais[0].status,
            StatusMaterial.DISPONIVEL,
        )

    def test_recusa_composicao_invalida_sem_mudar_originais(self):
        outro_usuario = Catador(
            "Outro",
            "outro@example.com",
            "hash",
            "000",
            "Rua",
            "11111111111",
        )

        for composicao in (
            [],
            [self.dados, self.dados],
            [self.dados | {"status": "DISPONIVEL"}],
            [self.dados | {"responsavelAtual": outro_usuario}],
            [
                self.dados | {"pesoKg": 50000},
                self.dados | {"identificador": str(uuid4())},
            ],
        ):
            with self.subTest(composicao=composicao):
                with self.assertRaises(ValueError):
                    LoteMaterial.reconstituir_ativo(
                        **(
                            self.lote_dados
                            | {"dadosMateriais": composicao}
                        )
                    )

        self.assertIs(
            self.original.loteAtual,
            self.lote_original,
        )
        self.assertEqual(
            len(self.original.obterHistorico()),
            2,
        )


if __name__ == "__main__":
    unittest.main()