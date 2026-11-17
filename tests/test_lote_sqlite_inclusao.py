import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.dao.lote_sqlite_dao import LoteSQLiteDAO
from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.model.enums import CategoriaMaterial, CondicaoMaterial
from app.model.material import Material, TipoMaterial
from app.model.usuario import Catador


class TestLoteSQLiteInclusao(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)

        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

        self.tipo = TipoMaterial(
            "PET", "Teste", CategoriaMaterial.PLASTICO
        )
        self.usuario = Catador(
            "Teste", "teste@example.com", "hash",
            "000", "Rua", "00000000000",
        )

        self.materiais = [
            Material(
                self.tipo,
                peso,
                CondicaoMaterial.LIMPO,
                self.usuario,
            )
            for peso in (10, 20)
        ]

        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(self.tipo)
            UsuarioSQLiteDAO(conexao).adicionar(self.usuario)

            for material in self.materiais:
                material.disponibilizar()
                MaterialSQLiteDAO(conexao).adicionar(material)

        self.lote = self.usuario.criarLote(self.materiais[0])
        self.lote.adicionarMaterial(self.materiais[1])
        self.lote.registrarPesagem(29)

    def conferir_reversao(self):
        with conectar(self.caminho) as conexao:
            for tabela in (
                "lotes",
                "lotes_materiais",
                "vinculos_lotes_atuais",
            ):
                total = conexao.execute(
                    f"SELECT COUNT(*) FROM {tabela}"
                ).fetchone()[0]

                self.assertEqual(total, 0)

            disponiveis = conexao.execute(
                "SELECT COUNT(*) FROM materiais "
                "WHERE status = 'DISPONIVEL'"
            ).fetchone()[0]

            eventos = conexao.execute(
                "SELECT COUNT(*) FROM eventos_rastreio"
            ).fetchone()[0]

            self.assertEqual(disponiveis, 2)
            self.assertEqual(eventos, 2)

    def test_grava_lote_composicao_vinculos_e_eventos(self):
        self.lote.disponibilizar()

        with conectar(self.caminho) as conexao:
            LoteSQLiteDAO(conexao).adicionar(self.lote)

        with conectar(self.caminho) as conexao:
            registro = conexao.execute(
                "SELECT * FROM lotes WHERE id = ?",
                (str(self.lote.id),),
            ).fetchone()

            self.assertEqual(registro["peso_registrado"], 29)
            self.assertEqual(registro["status"], "DISPONIVEL")
            self.assertEqual(
                registro["data_criacao"],
                self.lote.dataCriacao.isoformat(),
            )

            composicao = conexao.execute(
                "SELECT material_id FROM lotes_materiais "
                "ORDER BY ordem"
            ).fetchall()

            self.assertEqual(
                [r[0] for r in composicao],
                [str(m.id) for m in self.materiais],
            )

            vinculos = conexao.execute(
                "SELECT COUNT(*) FROM vinculos_lotes_atuais"
            ).fetchone()[0]

            agrupados = conexao.execute(
                "SELECT COUNT(*) FROM materiais "
                "WHERE status = 'EM_LOTE'"
            ).fetchone()[0]

            self.assertEqual(vinculos, 2)
            self.assertEqual(agrupados, 2)

            for material in self.materiais:
                eventos = conexao.execute(
                    "SELECT id FROM eventos_rastreio "
                    "WHERE material_id = ? ORDER BY ordem",
                    (str(material.id),),
                ).fetchall()

                self.assertEqual(
                    [r[0] for r in eventos],
                    [
                        str(e.id)
                        for e in material.obterHistorico()
                    ],
                )

    def test_recusa_duplicidade(self):
        with conectar(self.caminho) as conexao:
            dao = LoteSQLiteDAO(conexao)
            dao.adicionar(self.lote)

            with self.assertRaises(ValueError):
                dao.adicionar(self.lote)

            total = conexao.execute(
                "SELECT COUNT(*) FROM lotes"
            ).fetchone()[0]

            self.assertEqual(total, 1)

    def test_falha_no_segundo_material_desfaz_tudo(self):
        evento = self.materiais[1].obterHistorico()[-1]
        self.materiais[1].adicionarEvento(evento)

        with conectar(self.caminho) as conexao:
            with self.assertRaises(sqlite3.IntegrityError):
                LoteSQLiteDAO(conexao).adicionar(self.lote)

        self.conferir_reversao()

    def test_rollback_externo_desfaz_inclusao(self):
        with self.assertRaises(RuntimeError):
            with conectar(self.caminho) as conexao:
                LoteSQLiteDAO(conexao).adicionar(self.lote)
                raise RuntimeError("Falha posterior")

        self.conferir_reversao()

    def test_recusa_material_nao_persistido(self):
        material = Material(
            self.tipo,
            5,
            CondicaoMaterial.LIMPO,
            self.usuario,
        )
        material.disponibilizar()
        self.lote.adicionarMaterial(material)

        with conectar(self.caminho) as conexao:
            with self.assertRaises(ValueError):
                LoteSQLiteDAO(conexao).adicionar(self.lote)

        self.conferir_reversao()

    def test_recusa_lote_encerrado(self):
        self.lote.cancelar()

        with conectar(self.caminho) as conexao:
            with self.assertRaises(ValueError):
                LoteSQLiteDAO(conexao).adicionar(self.lote)

        self.conferir_reversao()


if __name__ == "__main__":
    unittest.main()