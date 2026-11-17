import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from uuid import uuid4

from app.dao.lote_dao import LoteDAO
from app.dao.lote_sqlite_dao import LoteSQLiteDAO
from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.model.enums import CategoriaMaterial, CondicaoMaterial
from app.model.material import Material, TipoMaterial
from app.model.usuario import Catador
from app.services.lote_service import (
    LoteService,
    AcessoLoteNegadoError,
    LoteNaoEncontradoError,
)


class TestLoteSQLiteListagem(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)

        self.caminho = Path(pasta.name) / "teste.sqlite3"
        inicializar_banco(self.caminho)

        tipo = TipoMaterial(
            "PET", "Teste", CategoriaMaterial.PLASTICO
        )

        self.usuarios = [
            Catador(
                nome, email, "hash",
                "000", "Rua", cpf,
            )
            for nome, email, cpf in (
                ("A", "a@example.com", "00000000000"),
                ("B", "b@example.com", "11111111111"),
            )
        ]

        self.lotes = []

        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(tipo)

            for usuario in self.usuarios:
                UsuarioSQLiteDAO(conexao).adicionar(usuario)

            dao = LoteSQLiteDAO(conexao)

            for usuario in (
                self.usuarios[0],
                self.usuarios[0],
                self.usuarios[1],
            ):
                material = Material(
                    tipo,
                    10,
                    CondicaoMaterial.LIMPO,
                    usuario,
                )
                material.disponibilizar()
                MaterialSQLiteDAO(conexao).adicionar(material)

                lote = usuario.criarLote(material)
                dao.adicionar(lote)
                self.lotes.append(lote)

            dao.cancelar(self.lotes[0].id)

            self.lotes[1].disponibilizar()
            dao.atualizar_pesagem_e_estado(self.lotes[1])

    def test_lista_por_criador_incluindo_encerrado(self):
        with conectar(self.caminho) as conexao:
            usuario = UsuarioSQLiteDAO(conexao).buscar_por_id(
                self.usuarios[0].id
            )

            servico = LoteService(
                LoteSQLiteDAO(conexao),
                MaterialSQLiteDAO(conexao),
            )

            lotes = servico.listar_do_usuario(usuario)

            self.assertEqual(
                [l.id for l in lotes],
                [l.id for l in self.lotes[:2]],
            )
            self.assertEqual(
                [
                    l.id
                    for l in servico.listar_do_usuario(
                        self.usuarios[1]
                    )
                ],
                [self.lotes[2].id],
            )

    def test_lista_somente_disponiveis_sem_gravar(self):
        with conectar(self.caminho) as conexao:
            antes = conexao.total_changes

            lotes = LoteSQLiteDAO(
                conexao
            ).listar_disponiveis()

            self.assertEqual(
                [l.id for l in lotes],
                [self.lotes[1].id],
            )
            self.assertEqual(
                conexao.total_changes,
                antes,
            )

    def test_busca_autoriza_uuid_e_recusa_outro_criador(self):
        with conectar(self.caminho) as conexao:
            servico = LoteService(
                LoteSQLiteDAO(conexao),
                MaterialSQLiteDAO(conexao),
            )

            lote = servico.buscar_do_usuario(
                self.lotes[1].id,
                self.usuarios[0],
            )

            self.assertIsNot(
                lote.criador,
                self.usuarios[0],
            )
            self.assertEqual(
                lote.criador.id,
                self.usuarios[0].id,
            )

            with self.assertRaises(AcessoLoteNegadoError):
                servico.buscar_do_usuario(
                    lote.id,
                    self.usuarios[1],
                )

            with self.assertRaises(LoteNaoEncontradoError):
                servico.buscar_do_usuario(
                    uuid4(),
                    self.usuarios[0],
                )

    def test_memoria_reconhece_usuario_reconstruido(self):
        with conectar(self.caminho) as conexao:
            usuario = UsuarioSQLiteDAO(conexao).buscar_por_id(
                self.usuarios[0].id
            )

        dao = LoteDAO(
            SimpleNamespace(lotes=self.lotes)
        )

        self.assertEqual(
            dao.listar_por_criador(usuario),
            self.lotes[:2],
        )

        servico = LoteService(dao, None)

        self.assertIs(
            servico.buscar_do_usuario(
                self.lotes[0].id,
                usuario,
            ),
            self.lotes[0],
        )


if __name__ == "__main__":
    unittest.main()