import unittest
from types import SimpleNamespace

from app.dao.ponto_coleta_dao import PontoColetaDAO
from app.dao.tipo_material_dao import TipoMaterialDAO
from app.model.coleta import PontoColeta
from app.model.enums import CategoriaMaterial, TipoPontoColeta
from app.model.material import TipoMaterial
from app.services.ponto_coleta_service import PontoColetaService


class TestPontoColetaService(unittest.TestCase):

    def setUp(self):
        self.pet = TipoMaterial(
            nome="PET",
            descricao="PET para testes",
            categoria=CategoriaMaterial.PLASTICO,
        )
        self.pp = TipoMaterial(
            nome="PP",
            descricao="PP para testes",
            categoria=CategoriaMaterial.PLASTICO,
        )

        self.ponto_pet = self.criar_ponto(
            "Ponto PET",
            [self.pet],
        )
        self.ponto_pp = self.criar_ponto(
            "Ponto PP",
            [self.pp],
        )

        self.repositorio = SimpleNamespace(
            pontos=[self.ponto_pet, self.ponto_pp],
            tipos=[self.pet, self.pp],
        )

        self.servico = PontoColetaService(
            PontoColetaDAO(self.repositorio),
            TipoMaterialDAO(self.repositorio),
        )

    def criar_ponto(self, nome, tipos):
        return PontoColeta(
            nome=nome,
            endereco="Endereço de teste",
            latitude=-16.68,
            longitude=-49.26,
            tipo=TipoPontoColeta.ECOPONTO,
            tiposAceitos=tipos,
        )

    def test_consulta_sem_filtro_lista_todos(self):
        pontos, selecionado = self.servico.consultar()

        self.assertEqual(
            pontos,
            [self.ponto_pet, self.ponto_pp],
        )
        self.assertIsNone(selecionado)

    def test_filtra_por_material_aceito(self):
        pontos, selecionado = self.servico.consultar(
            str(self.pet.id)
        )

        self.assertEqual(pontos, [self.ponto_pet])
        self.assertIs(selecionado, self.pet)

    def test_tipo_inexistente_preserva_consulta_sem_filtro(self):
        pontos, selecionado = self.servico.consultar(
            "id-inexistente"
        )

        self.assertEqual(
            pontos,
            [self.ponto_pet, self.ponto_pp],
        )
        self.assertIsNone(selecionado)

    def test_tipo_sem_pontos_retorna_lista_vazia(self):
        outro_tipo = TipoMaterial(
            nome="Outro plástico",
            descricao="Tipo sem ponto cadastrado",
            categoria=CategoriaMaterial.PLASTICO,
        )
        self.repositorio.tipos.append(outro_tipo)

        pontos, selecionado = self.servico.consultar(
            str(outro_tipo.id)
        )

        self.assertEqual(pontos, [])
        self.assertIs(selecionado, outro_tipo)

    def test_listas_retornadas_nao_apagam_armazenamento(self):
        pontos, _ = self.servico.consultar()
        tipos = self.servico.listar_tipos()

        pontos.clear()
        tipos.clear()

        self.assertEqual(
            self.repositorio.pontos,
            [self.ponto_pet, self.ponto_pp],
        )
        self.assertEqual(
            self.repositorio.tipos,
            [self.pet, self.pp],
        )


if __name__ == "__main__":
    unittest.main()