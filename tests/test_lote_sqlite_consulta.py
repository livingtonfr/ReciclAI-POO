import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.dao.lote_sqlite_dao import LoteSQLiteDAO
from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.model.enums import (
    CategoriaMaterial,
    CondicaoMaterial,
    StatusMaterial,
)
from app.model.material import (
    Material,
    TipoMaterial,
    AvaliacaoQualidade,
)
from app.model.usuario import Catador


class TestLoteSQLiteConsulta(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)

        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

        tipo = TipoMaterial(
            "PET", "Teste", CategoriaMaterial.PLASTICO
        )
        usuario = Catador(
            "Teste", "teste@example.com", "hash",
            "000", "Rua", "00000000000",
        )

        self.materiais = [
            Material(
                tipo,
                peso,
                CondicaoMaterial.LIMPO,
                usuario,
            )
            for peso in (10, 20)
        ]

        self.avaliacao = AvaliacaoQualidade(
            CondicaoMaterial.SUJO,
            0.9,
            "Teste",
        )
        self.materiais[0].adicionarAvaliacao(self.avaliacao)

        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(tipo)
            UsuarioSQLiteDAO(conexao).adicionar(usuario)

            for material in self.materiais:
                material.disponibilizar()
                MaterialSQLiteDAO(conexao).adicionar(material)

            self.lote = usuario.criarLote(self.materiais[0])
            self.lote.adicionarMaterial(self.materiais[1])
            self.lote.registrarPesagem(29)

            LoteSQLiteDAO(conexao).adicionar(self.lote)

    def test_reabre_e_reconstroi_composicao_e_identidades(self):
        with conectar(self.caminho) as conexao:
            lote = LoteSQLiteDAO(conexao).buscar_por_id(
                self.lote.id
            )

        self.assertIsNot(lote, self.lote)
        self.assertEqual(lote.id, self.lote.id)
        self.assertEqual(
            lote.dataCriacao,
            self.lote.dataCriacao,
        )
        self.assertEqual(lote.status, self.lote.status)
        self.assertEqual(lote.pesoRegistrado, 29)
        self.assertEqual(
            [m.id for m in lote.materiais],
            [m.id for m in self.materiais],
        )
        self.assertIs(
            lote.materiais[0].tipoMaterial,
            lote.materiais[1].tipoMaterial,
        )

        for material, original in zip(
            lote.materiais,
            self.materiais,
        ):
            self.assertIs(material.loteAtual, lote)
            self.assertIs(
                material.responsavelAtual,
                lote.criador,
            )
            self.assertIs(
                material.status,
                StatusMaterial.EM_LOTE,
            )
            self.assertEqual(
                material.dataRegistro,
                original.dataRegistro,
            )
            self.assertEqual(
                [e.id for e in material.obterHistorico()],
                [e.id for e in original.obterHistorico()],
            )

        avaliacao = lote.materiais[0].obterAvaliacoes()[0]

        self.assertEqual(avaliacao.id, self.avaliacao.id)
        self.assertEqual(
            avaliacao.dataAvaliacao,
            self.avaliacao.dataAvaliacao,
        )
        self.assertEqual(avaliacao.observacoes, "Teste")

    def test_consulta_nao_grava_e_busca_inexistente_retorna_none(self):
        with conectar(self.caminho) as conexao:
            dao = LoteSQLiteDAO(conexao)
            antes = conexao.total_changes

            dao.buscar_por_id(self.lote.id)
            dao.buscar_por_id(str(self.lote.id))

            self.assertIsNone(dao.buscar_por_id(uuid4()))
            self.assertIsNone(
                dao.buscar_por_id("' OR 1=1 --")
            )
            self.assertEqual(conexao.total_changes, antes)

    def test_recusa_vinculo_ausente(self):
        with conectar(self.caminho) as conexao:
            conexao.execute(
                "DELETE FROM vinculos_lotes_atuais "
                "WHERE material_id = ?",
                (str(self.materiais[0].id),),
            )

            with self.assertRaises(ValueError):
                LoteSQLiteDAO(conexao).buscar_por_id(
                    self.lote.id
                )

    def test_recusa_estado_incompativel_do_material(self):
        with conectar(self.caminho) as conexao:
            conexao.execute(
                "UPDATE materiais SET status = 'DISPONIVEL' "
                "WHERE id = ?",
                (str(self.materiais[0].id),),
            )

            with self.assertRaises(ValueError):
                LoteSQLiteDAO(conexao).buscar_por_id(
                    self.lote.id
                )

    def test_objeto_recuperado_permite_remocao_sem_gravacao_automatica(self):
        with conectar(self.caminho) as conexao:
            dao = LoteSQLiteDAO(conexao)
            lote = dao.buscar_por_id(self.lote.id)
            removido = lote.materiais[1]

            lote.removerMaterial(removido)

            self.assertIsNone(lote.pesoRegistrado)
            self.assertIsNone(removido.loteAtual)

            persistido = dao.buscar_por_id(self.lote.id)

            self.assertEqual(len(persistido.materiais), 2)
            self.assertEqual(persistido.pesoRegistrado, 29)


if __name__ == "__main__":
    unittest.main()