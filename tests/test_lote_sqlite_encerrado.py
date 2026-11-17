import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.dao.lote_sqlite_dao import LoteSQLiteDAO
from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.model.enums import (
    CategoriaMaterial,
    CondicaoMaterial,
    StatusLote,
)
from app.model.material import Material, TipoMaterial
from app.model.usuario import Catador


class TestLoteSQLiteEncerrado(unittest.TestCase):
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

        materiais = [
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

            for material in materiais:
                material.disponibilizar()
                MaterialSQLiteDAO(conexao).adicionar(material)

            lote = self.usuario.criarLote(materiais[0])
            lote.adicionarMaterial(materiais[1])
            lote.registrarPesagem(29)

            dao = LoteSQLiteDAO(conexao)
            dao.adicionar(lote)
            self.encerrado = dao.cancelar(lote.id)

    def test_recupera_cancelado_sem_vinculos(self):
        with conectar(self.caminho) as conexao:
            lote = LoteSQLiteDAO(conexao).buscar_por_id(
                self.encerrado.id
            )

        self.assertIs(lote.status, StatusLote.CANCELADO)
        self.assertEqual(lote.pesoRegistrado, 29)
        self.assertEqual(
            lote.dataCriacao,
            self.encerrado.dataCriacao,
        )
        self.assertEqual(
            [m.id for m in lote.materiais],
            [m.id for m in self.encerrado.materiais],
        )
        self.assertTrue(
            all(m.loteAtual is None for m in lote.materiais)
        )

    def test_preserva_vinculo_com_novo_lote_sem_gravar(self):
        materiais = self.encerrado.materiais

        novo = self.encerrado.criador.criarLote(
            materiais[0]
        )
        novo.adicionarMaterial(materiais[1])

        with conectar(self.caminho) as conexao:
            LoteSQLiteDAO(conexao).adicionar(novo)

        with conectar(self.caminho) as conexao:
            antes = conexao.total_changes

            antigo = LoteSQLiteDAO(conexao).buscar_por_id(
                self.encerrado.id
            )

            self.assertEqual(
                conexao.total_changes,
                antes,
            )

        atual = antigo.materiais[0].loteAtual

        self.assertEqual(atual.id, novo.id)
        self.assertIs(
            antigo.materiais[1].loteAtual,
            atual,
        )
        self.assertIs(
            atual.materiais[0],
            antigo.materiais[0],
        )
        self.assertIs(
            atual.materiais[1],
            antigo.materiais[1],
        )
        self.assertEqual(
            len(antigo.materiais[0].obterHistorico()),
            3,
        )

    def test_recusa_vinculo_apontando_para_encerrado(self):
        with conectar(self.caminho) as conexao:
            conexao.execute(
                "INSERT INTO vinculos_lotes_atuais "
                "(material_id, lote_id) VALUES (?, ?)",
                (
                    str(self.encerrado.materiais[0].id),
                    str(self.encerrado.id),
                ),
            )

            with self.assertRaises(ValueError):
                LoteSQLiteDAO(conexao).buscar_por_id(
                    self.encerrado.id
                )


if __name__ == "__main__":
    unittest.main()