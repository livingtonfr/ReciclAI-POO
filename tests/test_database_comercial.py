import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco


class TestDatabaseComercial(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)

        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

        self.vendedor = str(uuid4())
        self.comprador = str(uuid4())
        self.lote = str(uuid4())
        self.data = "2026-11-16T12:00:00"

        with conectar(self.caminho) as conexao:
            conexao.execute(
                """
                INSERT INTO usuarios (
                    id, perfil, nome, email, senha_hash,
                    telefone, endereco, criado_em, cpf
                ) VALUES (?, 'catador', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.vendedor,
                    "Vendedor",
                    "vendedor@example.com",
                    "hash",
                    "000",
                    "Rua",
                    self.data,
                    "00000000000",
                ),
            )

            conexao.execute(
                """
                INSERT INTO usuarios (
                    id, perfil, nome, email, senha_hash,
                    telefone, endereco, criado_em,
                    cnpj, status_validacao
                ) VALUES (
                    ?, 'empresa', ?, ?, ?, ?, ?, ?, ?, 'APROVADA'
                )
                """,
                (
                    self.comprador,
                    "Comprador",
                    "comprador@example.com",
                    "hash",
                    "000",
                    "Rua",
                    self.data,
                    "11111111111111",
                ),
            )

            conexao.execute(
                """
                INSERT INTO lotes (
                    id, criador_id, data_criacao, status
                ) VALUES (?, ?, ?, 'DISPONIVEL')
                """,
                (self.lote, self.vendedor, self.data),
            )

    def inserir_transacao(self, conexao, **alteracoes):
        dados = {
            "id": str(uuid4()),
            "lote_id": self.lote,
            "vendedor_id": self.vendedor,
            "comprador_id": self.comprador,
            "valor_total": 100.0,
            "data_transacao": self.data,
            "status": "PENDENTE",
            "peso_negociado": None,
        }
        dados.update(alteracoes)

        conexao.execute(
            """
            INSERT INTO transacoes (
                id, lote_id, vendedor_id, comprador_id,
                valor_total, data_transacao, status,
                peso_negociado
            ) VALUES (
                :id, :lote_id, :vendedor_id, :comprador_id,
                :valor_total, :data_transacao, :status,
                :peso_negociado
            )
            """,
            dados,
        )

        return dados["id"]

    def inserir_certificado(self, conexao, transacao_id, codigo):
        identificador = str(uuid4())

        conexao.execute(
            """
            INSERT INTO certificados (
                id, transacao_id, codigo, data_emissao
            ) VALUES (?, ?, ?, ?)
            """,
            (
                identificador,
                transacao_id,
                codigo,
                self.data,
            ),
        )

        return identificador

    def test_reinicializacao_preserva_registros(self):
        with conectar(self.caminho) as conexao:
            transacao_id = self.inserir_transacao(conexao)

        inicializar_banco(self.caminho)

        with conectar(self.caminho) as conexao:
            registro = conexao.execute(
                "SELECT * FROM transacoes WHERE id = ?",
                (transacao_id,),
            ).fetchone()

            self.assertIsNotNone(registro)
            self.assertEqual(registro["status"], "PENDENTE")
            self.assertEqual(registro["valor_total"], 100)
            self.assertEqual(
                conexao.execute(
                    "SELECT COUNT(*) FROM usuarios"
                ).fetchone()[0],
                2,
            )

    def test_recusa_referencias_inexistentes(self):
        with conectar(self.caminho) as conexao:
            for campo in (
                "lote_id",
                "vendedor_id",
                "comprador_id",
            ):
                with self.subTest(campo=campo):
                    with self.assertRaises(sqlite3.IntegrityError):
                        self.inserir_transacao(
                            conexao,
                            **{campo: str(uuid4())},
                        )

            with self.assertRaises(sqlite3.IntegrityError):
                self.inserir_certificado(
                    conexao,
                    str(uuid4()),
                    "CERT-INEXISTENTE",
                )

    def test_recusa_participantes_iguais_e_valores_invalidos(self):
        with conectar(self.caminho) as conexao:
            with self.assertRaises(sqlite3.IntegrityError):
                self.inserir_transacao(
                    conexao,
                    comprador_id=self.vendedor,
                )

            for valor in (0, -1, None, "abc", float("inf")):
                with self.subTest(valor=valor):
                    with self.assertRaises(sqlite3.IntegrityError):
                        self.inserir_transacao(
                            conexao,
                            valor_total=valor,
                        )

    def test_valida_estado_e_peso_negociado(self):
        invalidos = (
            ("DESCONHECIDO", None),
            ("PENDENTE", 10),
            ("CANCELADA", 10),
            ("CONCLUIDA", None),
            ("CONCLUIDA", 0),
            ("CONCLUIDA", -1),
            ("CONCLUIDA", 50001),
            ("CONCLUIDA", "abc"),
        )

        with conectar(self.caminho) as conexao:
            for estado, peso in invalidos:
                with self.subTest(estado=estado, peso=peso):
                    with self.assertRaises(sqlite3.IntegrityError):
                        self.inserir_transacao(
                            conexao,
                            status=estado,
                            peso_negociado=peso,
                        )

            self.inserir_transacao(
                conexao,
                status="CANCELADA",
            )
            self.inserir_transacao(
                conexao,
                status="CONCLUIDA",
                peso_negociado=50000,
            )

    def test_apenas_uma_concluida_por_lote(self):
        with conectar(self.caminho) as conexao:
            primeira = self.inserir_transacao(conexao)
            segunda = self.inserir_transacao(conexao)

            conexao.execute(
                """
                UPDATE transacoes
                SET status = 'CONCLUIDA', peso_negociado = 10
                WHERE id = ?
                """,
                (primeira,),
            )

            with self.assertRaises(sqlite3.IntegrityError):
                conexao.execute(
                    """
                    UPDATE transacoes
                    SET status = 'CONCLUIDA', peso_negociado = 10
                    WHERE id = ?
                    """,
                    (segunda,),
                )

            with self.assertRaises(sqlite3.IntegrityError):
                self.inserir_transacao(
                    conexao,
                    status="CONCLUIDA",
                    peso_negociado=10,
                )

            registro = conexao.execute(
                "SELECT status FROM transacoes WHERE id = ?",
                (segunda,),
            ).fetchone()

            self.assertEqual(registro["status"], "PENDENTE")

    def test_certificado_unico_por_transacao_e_codigo(self):
        with conectar(self.caminho) as conexao:
            primeira = self.inserir_transacao(
                conexao,
                status="CONCLUIDA",
                peso_negociado=10,
            )

            outro_lote = str(uuid4())

            conexao.execute(
                """
                INSERT INTO lotes (
                    id, criador_id, data_criacao, status
                ) VALUES (?, ?, ?, 'NEGOCIADO')
                """,
                (outro_lote, self.vendedor, self.data),
            )

            segunda = self.inserir_transacao(
                conexao,
                lote_id=outro_lote,
                status="CONCLUIDA",
                peso_negociado=20,
            )

            self.inserir_certificado(
                conexao,
                primeira,
                "CERT-001",
            )

            with self.assertRaises(sqlite3.IntegrityError):
                self.inserir_certificado(
                    conexao,
                    primeira,
                    "CERT-002",
                )

            with self.assertRaises(sqlite3.IntegrityError):
                self.inserir_certificado(
                    conexao,
                    segunda,
                    "CERT-001",
                )

            with self.assertRaises(sqlite3.IntegrityError):
                self.inserir_certificado(
                    conexao,
                    segunda,
                    "   ",
                )

            self.inserir_certificado(
                conexao,
                segunda,
                "CERT-002",
            )

    def test_rollback_externo_remove_transacao_e_certificado(self):
        with self.assertRaises(RuntimeError):
            with conectar(self.caminho) as conexao:
                transacao_id = self.inserir_transacao(
                    conexao,
                    status="CONCLUIDA",
                    peso_negociado=10,
                )

                self.inserir_certificado(
                    conexao,
                    transacao_id,
                    "CERT-ROLLBACK",
                )

                raise RuntimeError("Falha posterior")

        with conectar(self.caminho) as conexao:
            for tabela in ("transacoes", "certificados"):
                total = conexao.execute(
                    f"SELECT COUNT(*) FROM {tabela}"
                ).fetchone()[0]

                self.assertEqual(total, 0)


if __name__ == "__main__":
    unittest.main()