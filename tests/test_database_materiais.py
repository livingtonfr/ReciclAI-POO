import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco


class TestTabelasMateriais(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)

        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

        self.tipo_id = str(uuid4())
        self.usuario_id = str(uuid4())

        with conectar(self.caminho) as con:
            con.execute(
                "INSERT INTO tipos_material "
                "VALUES (?, ?, ?, ?, ?)",
                (self.tipo_id, "PET", "Teste", "PLASTICO", 1),
            )

            con.execute(
                "INSERT INTO usuarios "
                "(id, perfil, nome, email, senha_hash, telefone, "
                "endereco, criado_em, cpf) "
                "VALUES (?, 'catador', 'Teste', 'teste@example.com', "
                "'hash-teste', '000', 'Rua', "
                "'2026-11-16T12:00:00', '00000000000')",
                (self.usuario_id,),
            )

    def material(
        self, con, peso=10, tipo=None, responsavel=None,
        condicao="LIMPO", status="REGISTRADO",
    ):
        identificador = str(uuid4())

        con.execute(
            "INSERT INTO materiais "
            "(id, tipo_material_id, responsavel_atual_id, peso_kg, "
            "condicao_declarada, status, data_registro) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                identificador,
                tipo or self.tipo_id,
                responsavel or self.usuario_id,
                peso,
                condicao,
                status,
                "2026-11-16T12:00:00",
            ),
        )

        return identificador

    def evento(
        self, con, material_id, ordem=0, tipo="REGISTRO"
    ):
        con.execute(
            "INSERT INTO eventos_rastreio "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                str(uuid4()),
                material_id,
                ordem,
                tipo,
                "Teste",
                "2026-11-16T12:00:00",
            ),
        )

    def avaliacao(
        self, con, material_id, confianca=0.9, ordem=0
    ):
        con.execute(
            "INSERT INTO avaliacoes_qualidade "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid4()),
                material_id,
                ordem,
                "SUJO",
                confianca,
                None,
                "2026-11-16T12:00:00",
            ),
        )

    def test_preserva_registros_e_ordem_apos_reinicializar(self):
        with conectar(self.caminho) as con:
            material_id = self.material(con)

            self.evento(
                con, material_id, 1, "AGRUPAMENTO_LOTE"
            )
            self.evento(con, material_id, 0)
            self.avaliacao(con, material_id)

        inicializar_banco(self.caminho)

        with conectar(self.caminho) as con:
            eventos = con.execute(
                "SELECT tipo FROM eventos_rastreio "
                "WHERE material_id = ? ORDER BY ordem",
                (material_id,),
            ).fetchall()

            self.assertEqual(
                [evento[0] for evento in eventos],
                ["REGISTRO", "AGRUPAMENTO_LOTE"],
            )

            material = con.execute(
                "SELECT * FROM materiais"
            ).fetchone()

            self.assertEqual(material["id"], material_id)
            self.assertEqual(
                material["condicao_declarada"], "LIMPO"
            )

            avaliacao = con.execute(
                "SELECT * FROM avaliacoes_qualidade"
            ).fetchone()

            self.assertEqual(
                avaliacao["material_id"], material_id
            )
            self.assertEqual(
                avaliacao["condicao_detectada"], "SUJO"
            )

    def test_recusa_referencias_inexistentes(self):
        operacoes = (
            lambda con: self.material(
                con, tipo=str(uuid4())
            ),
            lambda con: self.material(
                con, responsavel=str(uuid4())
            ),
            lambda con: self.evento(con, str(uuid4())),
            lambda con: self.avaliacao(con, str(uuid4())),
        )

        for indice, operacao in enumerate(operacoes):
            with self.subTest(indice=indice):
                with self.assertRaises(sqlite3.IntegrityError):
                    with conectar(self.caminho) as con:
                        operacao(con)

    def test_valida_peso_condicao_e_status(self):
        casos = [
            {"peso": peso}
            for peso in (
                0, -1, 50001, float("inf"), float("nan")
            )
        ]
        casos += [
            {"condicao": "INVALIDA"},
            {"status": "INVALIDO"},
        ]

        for caso in casos:
            with self.subTest(caso=caso):
                with self.assertRaises(sqlite3.IntegrityError):
                    with conectar(self.caminho) as con:
                        self.material(con, **caso)

        with conectar(self.caminho) as con:
            self.material(con, peso=50000)

    def test_valida_confianca_e_ordem(self):
        with conectar(self.caminho) as con:
            material_id = self.material(con)
            self.evento(con, material_id)

            self.avaliacao(
                con, material_id, confianca=0, ordem=0
            )
            self.avaliacao(
                con, material_id, confianca=1, ordem=1
            )

        operacoes = [
            lambda con, valor=valor: self.avaliacao(
                con, material_id, valor, 2
            )
            for valor in (
                -0.1, 1.1, float("inf"), float("nan")
            )
        ]

        operacoes += [
            lambda con: self.evento(con, material_id, 0),
            lambda con: self.evento(con, material_id, -1),
            lambda con: self.evento(con, material_id, 1.5),
            lambda con: self.evento(
                con, material_id, 2, "INVALIDO"
            ),
            lambda con: self.avaliacao(
                con, material_id, ordem=0
            ),
        ]

        for indice, operacao in enumerate(operacoes):
            with self.subTest(indice=indice):
                with self.assertRaises(sqlite3.IntegrityError):
                    with conectar(self.caminho) as con:
                        operacao(con)

    def test_falha_no_evento_reverte_material(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with conectar(self.caminho) as con:
                material_id = self.material(con)
                self.evento(con, material_id)
                self.evento(con, material_id)

        with conectar(self.caminho) as con:
            total_materiais = con.execute(
                "SELECT COUNT(*) FROM materiais"
            ).fetchone()[0]

            total_eventos = con.execute(
                "SELECT COUNT(*) FROM eventos_rastreio"
            ).fetchone()[0]

            self.assertEqual(total_materiais, 0)
            self.assertEqual(total_eventos, 0)


if __name__ == "__main__":
    unittest.main()