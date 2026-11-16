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


class TestLoteSQLitePesagem(unittest.TestCase):
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

        materiais = [
            Material(
                tipo,
                peso,
                CondicaoMaterial.LIMPO,
                usuario,
            )
            for peso in (10, 20)
        ]

        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(tipo)
            UsuarioSQLiteDAO(conexao).adicionar(usuario)

            for material in materiais:
                material.disponibilizar()
                MaterialSQLiteDAO(conexao).adicionar(material)

            self.lote = usuario.criarLote(materiais[0])
            self.lote.adicionarMaterial(materiais[1])

            LoteSQLiteDAO(conexao).adicionar(self.lote)

    def recuperar(self):
        with conectar(self.caminho) as conexao:
            return LoteSQLiteDAO(conexao).buscar_por_id(
                self.lote.id
            )

    def test_persiste_pesagem_e_disponibilizacao(self):
        with conectar(self.caminho) as conexao:
            dao = LoteSQLiteDAO(conexao)
            lote = dao.buscar_por_id(self.lote.id)

            lote.registrarPesagem(29.5)
            lote.disponibilizar()

            dao.atualizar_pesagem_e_estado(lote)

        recuperado = self.recuperar()

        self.assertEqual(recuperado.pesoRegistrado, 29.5)
        self.assertIs(
            recuperado.status,
            StatusLote.DISPONIVEL,
        )
        self.assertEqual(
            recuperado.dataCriacao,
            self.lote.dataCriacao,
        )

        for material in recuperado.materiais:
            self.assertIs(material.loteAtual, recuperado)
            self.assertEqual(
                len(material.obterHistorico()),
                2,
            )

    def test_pesagem_invalida_preserva_valor_anterior(self):
        with conectar(self.caminho) as conexao:
            dao = LoteSQLiteDAO(conexao)
            lote = dao.buscar_por_id(self.lote.id)

            lote.registrarPesagem(28)
            dao.atualizar_pesagem_e_estado(lote)

            with self.assertRaises(ValueError):
                lote.registrarPesagem(0)

            dao.atualizar_pesagem_e_estado(lote)

        self.assertEqual(
            self.recuperar().pesoRegistrado,
            28,
        )

    def test_rollback_externo_reverte_pesagem_e_estado(self):
        with self.assertRaises(RuntimeError):
            with conectar(self.caminho) as conexao:
                dao = LoteSQLiteDAO(conexao)
                lote = dao.buscar_por_id(self.lote.id)

                lote.registrarPesagem(29)
                lote.disponibilizar()

                dao.atualizar_pesagem_e_estado(lote)

                raise RuntimeError("Falha posterior")

        recuperado = self.recuperar()

        self.assertIsNone(recuperado.pesoRegistrado)
        self.assertIs(
            recuperado.status,
            StatusLote.EM_FORMACAO,
        )

    def test_recusa_composicao_alterada(self):
        with conectar(self.caminho) as conexao:
            dao = LoteSQLiteDAO(conexao)
            lote = dao.buscar_por_id(self.lote.id)

            lote.removerMaterial(lote.materiais[1])

            with self.assertRaises(ValueError):
                dao.atualizar_pesagem_e_estado(lote)

        self.assertEqual(
            len(self.recuperar().materiais),
            2,
        )

    def test_recusa_retorno_a_formacao_e_cancelamento(self):
        with conectar(self.caminho) as conexao:
            dao = LoteSQLiteDAO(conexao)

            antigo = dao.buscar_por_id(self.lote.id)
            atual = dao.buscar_por_id(self.lote.id)

            atual.disponibilizar()
            dao.atualizar_pesagem_e_estado(atual)

            with self.assertRaises(ValueError):
                dao.atualizar_pesagem_e_estado(antigo)

            atual.cancelar()

            with self.assertRaises(ValueError):
                dao.atualizar_pesagem_e_estado(atual)

        self.assertIs(
            self.recuperar().status,
            StatusLote.DISPONIVEL,
        )


if __name__ == "__main__":
    unittest.main()