import unittest
from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

from app.model.enums import (
    CategoriaMaterial,
    CondicaoMaterial,
    StatusLote,
)
from app.model.lote import LoteMaterial
from app.model.material import Material, TipoMaterial
from app.model.usuario import Catador


class TestLoteReconstituicao(unittest.TestCase):
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
        self.material = Material(
            self.tipo,
            10,
            CondicaoMaterial.LIMPO,
            self.usuario,
        )
        self.material.disponibilizar()

        self.dados = dict(
            identificador=str(uuid4()),
            criador=self.usuario,
            dataCriacao="2026-01-01T10:00:00",
            status="CANCELADO",
            materiais=[self.material],
            pesoRegistrado=9.5,
        )

    def test_preserva_metadados_sem_executar_construtor(self):
        with patch.object(
            LoteMaterial,
            "__init__",
            side_effect=AssertionError("Construtor chamado"),
        ):
            lote = LoteMaterial.reconstituir_encerrado(
                **self.dados
            )

        self.assertEqual(
            str(lote.id),
            self.dados["identificador"],
        )
        self.assertEqual(
            lote.dataCriacao,
            datetime.fromisoformat(self.dados["dataCriacao"]),
        )
        self.assertIs(lote.criador, self.usuario)
        self.assertIs(lote.status, StatusLote.CANCELADO)
        self.assertEqual(lote.pesoRegistrado, 9.5)
        self.assertEqual(lote.calcularPesoTotal(), 10)

    def test_preserva_vinculo_com_outro_lote_e_historico(self):
        atual = self.usuario.criarLote(self.material)
        eventos = self.material.obterHistorico()

        lote = LoteMaterial.reconstituir_encerrado(
            **(self.dados | {"status": "NEGOCIADO"})
        )

        self.assertIs(lote.materiais[0], self.material)
        self.assertIs(self.material.loteAtual, atual)
        self.assertEqual(
            self.material.obterHistorico(),
            eventos,
        )
        self.assertIs(lote.status, StatusLote.NEGOCIADO)

    def test_copia_composicao_e_preserva_ordem(self):
        outro = Material(
            self.tipo,
            20,
            CondicaoMaterial.LIMPO,
            self.usuario,
        )
        self.dados["materiais"].append(outro)

        lote = LoteMaterial.reconstituir_encerrado(
            **self.dados
        )

        self.dados["materiais"].clear()
        lote.materiais.clear()

        self.assertEqual(
            lote.materiais,
            [self.material, outro],
        )

    def test_recusa_dados_invalidos_sem_alterar_material(self):
        for alteracao in (
            {"status": "EM_FORMACAO"},
            {"status": "DISPONIVEL"},
            {"identificador": "invalido"},
            {"dataCriacao": "invalida"},
            {"criador": None},
            {"materiais": []},
            {"materiais": [self.material, self.material]},
            {"pesoRegistrado": 0},
            {"pesoRegistrado": float("inf")},
        ):
            with self.subTest(alteracao=alteracao):
                with self.assertRaises(ValueError):
                    LoteMaterial.reconstituir_encerrado(
                        **(self.dados | alteracao)
                    )

        self.assertIsNone(self.material.loteAtual)
        self.assertEqual(
            len(self.material.obterHistorico()),
            1,
        )

    def test_lote_encerrado_continua_recusando_pesagem_e_composicao(self):
        lote = LoteMaterial.reconstituir_encerrado(
            **(self.dados | {"pesoRegistrado": None})
        )

        self.assertIsNone(lote.pesoRegistrado)

        with self.assertRaises(ValueError):
            lote.registrarPesagem(10)

        with self.assertRaises(ValueError):
            lote.adicionarMaterial(self.material)


if __name__ == "__main__":
    unittest.main()