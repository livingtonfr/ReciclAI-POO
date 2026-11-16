import unittest
from datetime import time

from app.model.coleta import (
    HorarioFuncionamento,
    PontoColeta,
)
from app.model.enums import DiaSemana, TipoPontoColeta


class TestHorariosColeta(unittest.TestCase):

    def criar_ponto(self, nome, horarios=None):
        return PontoColeta(
            nome=nome,
            endereco="Endereço de teste",
            latitude=-16.68,
            longitude=-49.26,
            tipo=TipoPontoColeta.ECOPONTO,
            horarios=horarios,
        )

    def test_pontos_possuem_objetos_de_horario_distintos(self):
        horario = HorarioFuncionamento(
            DiaSemana.SEGUNDA,
            time(8, 0),
            time(18, 0),
        )

        ponto_a = self.criar_ponto("Ponto A", [horario])
        ponto_b = self.criar_ponto("Ponto B", [horario])

        horario_a = ponto_a.horarios[0]
        horario_b = ponto_b.horarios[0]

        self.assertIsNot(horario_a, horario)
        self.assertIsNot(horario_b, horario)
        self.assertIsNot(horario_a, horario_b)

        for copia in (horario_a, horario_b):
            self.assertEqual(copia.diaSemana, DiaSemana.SEGUNDA)
            self.assertEqual(copia.horaAbertura, time(8, 0))
            self.assertEqual(copia.horaFechamento, time(18, 0))

    def test_alterar_listas_externas_nao_apaga_horarios(self):
        horario = HorarioFuncionamento(
            DiaSemana.SEGUNDA,
            "08:00",
            "18:00",
        )
        lista_original = [horario]
        ponto = self.criar_ponto("Ponto A", lista_original)

        lista_original.clear()
        self.assertEqual(len(ponto.horarios), 1)

        lista_recebida = ponto.horarios
        lista_recebida.clear()
        self.assertEqual(len(ponto.horarios), 1)

    def test_ponto_pode_ser_criado_sem_horarios(self):
        ponto = self.criar_ponto("Ponto sem horário")

        self.assertEqual(ponto.horarios, [])

    def test_recusa_elemento_que_nao_e_horario(self):
        with self.assertRaisesRegex(
            ValueError,
            "HorarioFuncionamento",
        ):
            self.criar_ponto(
                "Ponto inválido",
                ["Segunda, das 8h às 18h"],
            )

    def test_recusa_fechamento_anterior_ou_igual_a_abertura(self):
        for fechamento in ("07:00", "08:00"):
            with self.subTest(fechamento=fechamento):
                with self.assertRaises(ValueError):
                    HorarioFuncionamento(
                        DiaSemana.SEGUNDA,
                        "08:00",
                        fechamento,
                    )


if __name__ == "__main__":
    unittest.main()