import unittest
from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

from app.model.enums import (
    CategoriaMaterial,
    CondicaoMaterial,
    StatusMaterial,
    TipoEventoRastreio,
)
from app.model.material import (
    Material,
    TipoMaterial,
    EventoRastreio,
    AvaliacaoQualidade,
)
from app.model.usuario import Catador


class TestReconstituicaoMaterial(unittest.TestCase):
    def setUp(self):
        self.data = "2020-01-02T03:04:05.123456"

        self.tipo = TipoMaterial(
            "PET",
            "Teste",
            CategoriaMaterial.PLASTICO,
        )

        self.usuario = Catador(
            "Teste",
            "teste@example.com",
            "hash-teste",
            "000",
            "Rua",
            "00000000000",
        )

        self.evento_id = uuid4()
        self.avaliacao_id = uuid4()

        self.evento = EventoRastreio.reconstituir(
            self.evento_id,
            "REGISTRO",
            "Original",
            self.data,
        )

        self.avaliacao = AvaliacaoQualidade.reconstituir(
            self.avaliacao_id,
            "SUJO",
            0.9,
            self.data,
            "Observação original",
        )

        self.dados = dict(
            identificador=str(uuid4()),
            tipoMaterial=self.tipo,
            pesoKg=10,
            condicaoDeclarada="LIMPO",
            responsavelAtual=self.usuario,
            status="DISPONIVEL",
            dataRegistro=self.data,
            eventos=[self.evento],
            avaliacoes=[self.avaliacao],
            observacoesDeclaradas="Declaração original",
        )

    def test_evento_e_avaliacao_preservam_dados(self):
        self.assertEqual(self.evento.id, self.evento_id)
        self.assertIs(
            self.evento.tipo,
            TipoEventoRastreio.REGISTRO,
        )
        self.assertEqual(self.evento.descricao, "Original")
        self.assertEqual(
            self.evento.dataEvento,
            datetime.fromisoformat(self.data),
        )

        self.assertEqual(self.avaliacao.id, self.avaliacao_id)
        self.assertIs(
            self.avaliacao.condicaoDetectada,
            CondicaoMaterial.SUJO,
        )
        self.assertEqual(self.avaliacao.confianca, 0.9)
        self.assertEqual(
            self.avaliacao.observacoes,
            "Observação original",
        )
        self.assertEqual(
            self.avaliacao.dataAvaliacao,
            datetime.fromisoformat(self.data),
        )

    def test_material_preserva_dados_sem_executar_construtor(self):
        with patch.object(
            Material,
            "__init__",
            side_effect=AssertionError("Construtor chamado"),
        ):
            material = Material.reconstituir(**self.dados)

        self.assertEqual(
            str(material.id),
            self.dados["identificador"],
        )
        self.assertEqual(
            material.dataRegistro,
            datetime.fromisoformat(self.data),
        )
        self.assertEqual(material.pesoKg, 10)
        self.assertIs(material.tipoMaterial, self.tipo)
        self.assertIs(material.responsavelAtual, self.usuario)
        self.assertIs(
            material.status,
            StatusMaterial.DISPONIVEL,
        )
        self.assertIs(
            material.condicaoDeclarada,
            CondicaoMaterial.LIMPO,
        )
        self.assertEqual(
            material.observacoesDeclaradas,
            "Declaração original",
        )
        self.assertIsNone(material.loteAtual)
        self.assertEqual(
            material.obterHistorico(),
            [self.evento],
        )
        self.assertEqual(
            material.obterAvaliacoes(),
            [self.avaliacao],
        )

    def test_listas_preservam_ordem_e_nao_sao_compartilhadas(self):
        outro = EventoRastreio.reconstituir(
            uuid4(),
            "TRANSFERENCIA",
            "Segundo",
            self.data,
        )
        self.dados["eventos"].append(outro)

        material = Material.reconstituir(**self.dados)

        self.dados["eventos"].clear()
        self.dados["avaliacoes"].clear()
        material.obterHistorico().clear()
        material.obterAvaliacoes().clear()

        self.assertEqual(
            material.obterHistorico(),
            [self.evento, outro],
        )
        self.assertEqual(
            material.obterAvaliacoes(),
            [self.avaliacao],
        )

    def test_recusa_dados_invalidos_e_em_lote(self):
        casos = (
            {"pesoKg": 0},
            {"pesoKg": float("inf")},
            {"identificador": "id-invalido"},
            {"dataRegistro": "data-invalida"},
            {"status": "INVALIDO"},
            {"status": "EM_LOTE"},
            {"condicaoDeclarada": "INVALIDA"},
            {"tipoMaterial": None},
            {"responsavelAtual": None},
            {"eventos": [object()]},
            {"avaliacoes": [object()]},
        )

        for alteracao in casos:
            with self.subTest(alteracao=alteracao):
                with self.assertRaises((ValueError, TypeError)):
                    Material.reconstituir(
                        **(self.dados | alteracao)
                    )

        with self.assertRaises(ValueError):
            AvaliacaoQualidade.reconstituir(
                uuid4(),
                "LIMPO",
                1.1,
                self.data,
            )

        with self.assertRaises(ValueError):
            EventoRastreio.reconstituir(
                uuid4(),
                "INVALIDO",
                "Teste",
                self.data,
            )

    def test_estados_restaurados_preservam_regras(self):
        material = Material.reconstituir(
            **(self.dados | {"status": "REGISTRADO"})
        )

        material.disponibilizar()

        self.assertIs(
            material.status,
            StatusMaterial.DISPONIVEL,
        )
        self.assertEqual(len(material.obterHistorico()), 1)

        destinado = Material.reconstituir(
            **(self.dados | {"status": "DESTINADO"})
        )

        with self.assertRaises(ValueError):
            destinado.disponibilizar()

        self.assertIs(
            destinado.status,
            StatusMaterial.DESTINADO,
        )


if __name__ == "__main__":
    unittest.main()