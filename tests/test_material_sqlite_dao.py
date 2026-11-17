import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.model.enums import CategoriaMaterial, CondicaoMaterial
from app.model.material import Material, TipoMaterial, AvaliacaoQualidade
from app.model.usuario import Catador


class TestMaterialSQLiteDAO(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)

        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

        self.tipo = TipoMaterial(
            "PET",
            "Teste",
            CategoriaMaterial.PLASTICO,
        )

        self.usuario = Catador(
            "Teste",
            "teste@example.com",
            "hash",
            "000",
            "Rua",
            "00000000000",
        )

        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(self.tipo)
            UsuarioSQLiteDAO(conexao).adicionar(self.usuario)

        self.material = self.criar_material()

    def criar_material(self):
        return Material(
            self.tipo,
            10,
            CondicaoMaterial.LIMPO,
            self.usuario,
        )

    def test_recupera_dados_historico_e_avaliacoes_apos_reabrir(self):
        self.material.disponibilizar()
        self.material.transferirResponsabilidade(self.usuario)

        for condicao in (
            CondicaoMaterial.SUJO,
            CondicaoMaterial.LIMPO,
        ):
            self.material.adicionarAvaliacao(
                AvaliacaoQualidade(condicao, 0.9, "Teste")
            )

        with conectar(self.caminho) as conexao:
            MaterialSQLiteDAO(conexao).adicionar(self.material)

        with conectar(self.caminho) as conexao:
            recuperado = MaterialSQLiteDAO(conexao).buscar_por_id(
                self.material.id
            )

        for atributo in (
            "id",
            "pesoKg",
            "status",
            "dataRegistro",
            "condicaoDeclarada",
            "observacoesDeclaradas",
        ):
            self.assertEqual(
                getattr(recuperado, atributo),
                getattr(self.material, atributo),
            )

        self.assertEqual(recuperado.tipoMaterial.id, self.tipo.id)
        self.assertEqual(
            recuperado.responsavelAtual.id,
            self.usuario.id,
        )
        self.assertIsNot(recuperado, self.material)

        for metodo, atributos in (
            (
                "obterHistorico",
                ("id", "tipo", "descricao", "dataEvento"),
            ),
            (
                "obterAvaliacoes",
                (
                    "id",
                    "condicaoDetectada",
                    "confianca",
                    "observacoes",
                    "dataAvaliacao",
                ),
            ),
        ):
            original = getattr(self.material, metodo)()
            restaurado = getattr(recuperado, metodo)()

            self.assertEqual(len(restaurado), len(original))

            for antes, depois in zip(original, restaurado):
                for atributo in atributos:
                    self.assertEqual(
                        getattr(antes, atributo),
                        getattr(depois, atributo),
                    )

    def test_consultas_filtram_por_id_e_responsavel(self):
        with conectar(self.caminho) as conexao:
            dao = MaterialSQLiteDAO(conexao)
            dao.adicionar(self.material)

            usuario = UsuarioSQLiteDAO(conexao).buscar_por_id(
                self.usuario.id
            )

            self.assertEqual(
                [m.id for m in dao.listar_por_responsavel(usuario)],
                [self.material.id],
            )

            outro = Catador(
                "Outro",
                "outro@example.com",
                "hash",
                "000",
                "Rua",
                "11111111111",
            )

            self.assertEqual(
                dao.listar_por_responsavel(outro),
                [],
            )
            self.assertIsNone(dao.buscar_por_id(uuid4()))
            self.assertIsNone(
                dao.buscar_por_id("' OR 1=1 --")
            )

    def test_duplicidade_nao_altera_material_existente(self):
        with conectar(self.caminho) as conexao:
            dao = MaterialSQLiteDAO(conexao)
            dao.adicionar(self.material)

            with self.assertRaises(ValueError):
                dao.adicionar(self.material)

            recuperado = dao.buscar_por_id(self.material.id)

            self.assertEqual(
                len(recuperado.obterHistorico()),
                1,
            )

    def test_falha_em_avaliacao_desfaz_insercao_inteira(self):
        avaliacao = AvaliacaoQualidade(
            CondicaoMaterial.LIMPO,
            0.9,
        )

        self.material.adicionarAvaliacao(avaliacao)
        self.material.adicionarAvaliacao(avaliacao)

        with conectar(self.caminho) as conexao:
            dao = MaterialSQLiteDAO(conexao)

            with self.assertRaises(sqlite3.IntegrityError):
                dao.adicionar(self.material)

            self.assertIsNone(
                dao.buscar_por_id(self.material.id)
            )

            for tabela in (
                "eventos_rastreio",
                "avaliacoes_qualidade",
            ):
                total = conexao.execute(
                    f"SELECT COUNT(*) FROM {tabela}"
                ).fetchone()[0]

                self.assertEqual(total, 0)

            self.assertIsNotNone(
                UsuarioSQLiteDAO(conexao).buscar_por_id(
                    self.usuario.id
                )
            )

    def test_rollback_externo_desfaz_adicao(self):
        with self.assertRaises(RuntimeError):
            with conectar(self.caminho) as conexao:
                MaterialSQLiteDAO(conexao).adicionar(
                    self.material
                )
                raise RuntimeError("Falha posterior")

        with conectar(self.caminho) as conexao:
            self.assertIsNone(
                MaterialSQLiteDAO(conexao).buscar_por_id(
                    self.material.id
                )
            )

    def test_recusa_material_em_lote(self):
        self.material.disponibilizar()
        self.usuario.criarLote(self.material)

        with conectar(self.caminho) as conexao:
            dao = MaterialSQLiteDAO(conexao)

            with self.assertRaises(ValueError):
                dao.adicionar(self.material)

            self.assertIsNone(
                dao.buscar_por_id(self.material.id)
            )

    def test_rejeita_referencia_nao_persistida(self):
        tipo = TipoMaterial(
            "Vidro",
            "Teste",
            CategoriaMaterial.VIDRO,
        )
        material = Material(
            tipo,
            10,
            CondicaoMaterial.LIMPO,
            self.usuario,
        )

        with conectar(self.caminho) as conexao:
            dao = MaterialSQLiteDAO(conexao)

            with self.assertRaises(sqlite3.IntegrityError):
                dao.adicionar(material)

            self.assertIsNone(
                dao.buscar_por_id(material.id)
            )


if __name__ == "__main__":
    unittest.main()