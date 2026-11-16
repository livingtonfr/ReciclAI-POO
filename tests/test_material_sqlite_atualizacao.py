import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

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


class TestAtualizacaoMaterialSQLite(unittest.TestCase):
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
        self.material = Material(
            self.tipo,
            10,
            CondicaoMaterial.LIMPO,
            self.usuario,
        )

        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(self.tipo)
            UsuarioSQLiteDAO(conexao).adicionar(self.usuario)
            MaterialSQLiteDAO(conexao).adicionar(self.material)

    def recuperar(self):
        with conectar(self.caminho) as conexao:
            return MaterialSQLiteDAO(conexao).buscar_por_id(
                self.material.id
            )

    def test_atualiza_estado_e_avaliacao_sem_duplicar(self):
        avaliacao = AvaliacaoQualidade(
            CondicaoMaterial.SUJO,
            0.9,
            "Teste",
        )

        with conectar(self.caminho) as conexao:
            dao = MaterialSQLiteDAO(conexao)
            material = dao.buscar_por_id(self.material.id)

            material.disponibilizar()
            material.adicionarAvaliacao(avaliacao)

            dao.atualizar(material)
            dao.atualizar(material)

        recuperado = self.recuperar()

        self.assertIs(
            recuperado.status,
            StatusMaterial.DISPONIVEL,
        )
        self.assertEqual(
            recuperado.dataRegistro,
            self.material.dataRegistro,
        )
        self.assertEqual(
            [e.id for e in recuperado.obterHistorico()],
            [e.id for e in self.material.obterHistorico()],
        )
        self.assertEqual(
            [a.id for a in recuperado.obterAvaliacoes()],
            [avaliacao.id],
        )

    def test_falha_desfaz_estado_e_avaliacoes(self):
        self.material.disponibilizar()

        avaliacao = AvaliacaoQualidade(
            CondicaoMaterial.LIMPO,
            0.9,
        )
        self.material.adicionarAvaliacao(avaliacao)
        self.material.adicionarAvaliacao(avaliacao)

        with conectar(self.caminho) as conexao:
            with self.assertRaises(sqlite3.IntegrityError):
                MaterialSQLiteDAO(conexao).atualizar(
                    self.material
                )

        recuperado = self.recuperar()

        self.assertIs(
            recuperado.status,
            StatusMaterial.REGISTRADO,
        )
        self.assertEqual(recuperado.obterAvaliacoes(), [])

    def test_rollback_externo_preserva_estado_original(self):
        self.material.disponibilizar()

        with self.assertRaises(RuntimeError):
            with conectar(self.caminho) as conexao:
                MaterialSQLiteDAO(conexao).atualizar(
                    self.material
                )
                raise RuntimeError("Falha posterior")

        self.assertIs(
            self.recuperar().status,
            StatusMaterial.REGISTRADO,
        )

    def test_recusa_objeto_com_historico_desatualizado(self):
        antigo = self.recuperar()
        atual = self.recuperar()

        atual.adicionarAvaliacao(
            AvaliacaoQualidade(
                CondicaoMaterial.SUJO,
                0.8,
            )
        )

        with conectar(self.caminho) as conexao:
            dao = MaterialSQLiteDAO(conexao)
            dao.atualizar(atual)

            with self.assertRaises(ValueError):
                dao.atualizar(antigo)

        self.assertEqual(
            len(self.recuperar().obterAvaliacoes()),
            1,
        )

    def test_persiste_transferencia_e_seu_evento(self):
        outro = Catador(
            "Outro",
            "outro@example.com",
            "hash",
            "000",
            "Rua",
            "11111111111",
        )

        self.material.transferirResponsabilidade(outro)

        with conectar(self.caminho) as conexao:
            UsuarioSQLiteDAO(conexao).adicionar(outro)
            MaterialSQLiteDAO(conexao).atualizar(
                self.material
            )

        recuperado = self.recuperar()

        self.assertEqual(
            recuperado.responsavelAtual.id,
            outro.id,
        )
        self.assertEqual(
            [e.id for e in recuperado.obterHistorico()],
            [e.id for e in self.material.obterHistorico()],
        )

    def test_recusa_material_inexistente(self):
        outro = Material(
            self.tipo,
            20,
            CondicaoMaterial.LIMPO,
            self.usuario,
        )

        with conectar(self.caminho) as conexao:
            with self.assertRaises(ValueError):
                MaterialSQLiteDAO(conexao).atualizar(outro)


if __name__ == "__main__":
    unittest.main()