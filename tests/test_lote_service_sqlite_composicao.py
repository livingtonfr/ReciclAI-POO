import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from app.dao.lote_dao import LoteDAO
from app.dao.material_dao import MaterialDAO
from app.dao.lote_sqlite_dao import LoteSQLiteDAO
from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.database.conexao import conectar
from app.database.inicializacao import inicializar_banco
from app.model.enums import CategoriaMaterial, CondicaoMaterial, StatusMaterial
from app.model.material import Material, TipoMaterial
from app.model.usuario import Catador
from app.services.lote_service import LoteService, AcessoLoteNegadoError


class TestLoteServiceSQLiteComposicao(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.caminho = Path(pasta.name) / 'teste.sqlite3'
        inicializar_banco(self.caminho)
        self.usuario = Catador('A', 'a@example.com', 'hash', '000', 'Rua', '00000000000')
        self.outro = Catador('B', 'b@example.com', 'hash', '000', 'Rua', '11111111111')
        tipo = TipoMaterial('PET', 'Teste', CategoriaMaterial.PLASTICO)
        self.materiais = [
            Material(tipo, peso, CondicaoMaterial.LIMPO, self.usuario)
            for peso in (10, 20)
        ]
        with conectar(self.caminho) as conexao:
            TipoMaterialSQLiteDAO(conexao).adicionar(tipo)
            for usuario in (self.usuario, self.outro):
                UsuarioSQLiteDAO(conexao).adicionar(usuario)
            for material in self.materiais:
                material.disponibilizar()
                MaterialSQLiteDAO(conexao).adicionar(material)

    def servico(self, conexao):
        return LoteService(LoteSQLiteDAO(conexao), MaterialSQLiteDAO(conexao))

    def criar(self):
        with conectar(self.caminho) as conexao:
            return self.servico(conexao).criar(self.usuario, self.materiais[0].id)

    def test_criacao_e_filtro_com_material_ja_agrupado(self):
        lote = self.criar()
        self.assertIs(lote.criador, lote.materiais[0].responsavelAtual)
        with conectar(self.caminho) as conexao:
            servico = self.servico(conexao)
            recuperado = servico.buscar_do_usuario(lote.id, self.usuario)
            self.assertIs(recuperado.materiais[0].loteAtual, recuperado)
            self.assertEqual(
                [m.id for m in servico.listar_materiais_disponiveis(self.usuario)],
                [self.materiais[1].id],
            )
            self.assertEqual(servico.listar_materiais_disponiveis(
                self.usuario, excluir=self.materiais[1]), [])

    def test_inclusao_remocao_e_pesagem_apos_reabrir(self):
        lote = self.criar()
        with conectar(self.caminho) as conexao:
            dao = LoteSQLiteDAO(conexao)
            lote.registrarPesagem(10)
            dao.atualizar_pesagem_e_estado(lote)
            incluido = self.servico(conexao).adicionar_material(
                lote.id, self.materiais[1].id, self.usuario)
            self.assertIs(incluido.materiais[1].loteAtual, incluido)
        with conectar(self.caminho) as conexao:
            servico = self.servico(conexao)
            recuperado = servico.buscar_do_usuario(lote.id, self.usuario)
            self.assertEqual(recuperado.calcularPesoTotal(), 30)
            self.assertIsNone(recuperado.pesoRegistrado)
            servico.remover_material(lote.id, self.materiais[1].id, self.usuario)
        with conectar(self.caminho) as conexao:
            self.assertEqual(len(LoteSQLiteDAO(conexao).buscar_por_id(lote.id).materiais), 1)
            material = MaterialSQLiteDAO(conexao).buscar_por_id(self.materiais[1].id)
            self.assertIs(material.status, StatusMaterial.DISPONIVEL)
            self.assertEqual(len(material.obterHistorico()), 2)

    def test_recusas_nao_gravam(self):
        lote = self.criar()
        with conectar(self.caminho) as conexao:
            servico = self.servico(conexao)
            antes = conexao.total_changes
            with self.assertRaises(AcessoLoteNegadoError):
                servico.adicionar_material(lote.id, self.materiais[1].id, self.outro)
            with self.assertRaises(AcessoLoteNegadoError):
                servico.remover_material(lote.id, self.materiais[0].id, self.outro)
            with self.assertRaises(ValueError):
                servico.criar(self.outro, self.materiais[1].id)
            with self.assertRaises(ValueError):
                servico.remover_material(lote.id, self.materiais[0].id, self.usuario)
            self.assertEqual(conexao.total_changes, antes)

    def test_falha_sql_na_criacao_nao_deixa_lote_ou_evento(self):
        with conectar(self.caminho) as conexao:
            conexao.execute(
                "CREATE TEMP TRIGGER falhar BEFORE INSERT ON vinculos_lotes_atuais "
                "BEGIN SELECT RAISE(ABORT, 'Falha simulada'); END")
            with self.assertRaises(sqlite3.IntegrityError):
                self.servico(conexao).criar(self.usuario, self.materiais[0].id)
        with conectar(self.caminho) as conexao:
            self.assertEqual(conexao.execute('SELECT COUNT(*) FROM lotes').fetchone()[0], 0)
            material = MaterialSQLiteDAO(conexao).buscar_por_id(self.materiais[0].id)
            self.assertIs(material.status, StatusMaterial.DISPONIVEL)
            self.assertEqual(len(material.obterHistorico()), 1)

    def test_rollback_externo_da_composicao(self):
        lote = self.criar()
        with self.assertRaises(RuntimeError):
            with conectar(self.caminho) as conexao:
                self.servico(conexao).adicionar_material(lote.id, self.materiais[1].id, self.usuario)
                raise RuntimeError('Falha posterior')
        with conectar(self.caminho) as conexao:
            self.assertEqual(len(LoteSQLiteDAO(conexao).buscar_por_id(lote.id).materiais), 1)
            material = MaterialSQLiteDAO(conexao).buscar_por_id(self.materiais[1].id)
            self.assertIs(material.status, StatusMaterial.DISPONIVEL)
            self.assertEqual(len(material.obterHistorico()), 1)

    def test_memoria_preserva_instancias_com_usuario_reconstruido(self):
        with conectar(self.caminho) as conexao:
            usuario = UsuarioSQLiteDAO(conexao).buscar_por_id(self.usuario.id)
        repositorio = SimpleNamespace(materiais=self.materiais, lotes=[])
        servico = LoteService(LoteDAO(repositorio), MaterialDAO(repositorio))
        lote = servico.criar(usuario, self.materiais[0].id)
        self.assertIs(lote.criador, self.usuario)
        self.assertIs(servico.adicionar_material(lote.id, self.materiais[1].id, usuario), lote)
        self.assertIs(lote.materiais[1], self.materiais[1])
        servico.remover_material(lote.id, self.materiais[1].id, usuario)
        self.assertIsNone(self.materiais[1].loteAtual)


if __name__ == '__main__':
    unittest.main()
