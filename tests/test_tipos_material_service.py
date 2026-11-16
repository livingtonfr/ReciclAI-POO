import unittest
from types import SimpleNamespace

from app.dao.material_dao import MaterialDAO
from app.dao.tipo_material_dao import TipoMaterialDAO
from app.model.enums import CategoriaMaterial
from app.model.material import TipoMaterial
from app.services.material_service import MaterialService


class TestTiposMaterialService(unittest.TestCase):

    def setUp(self):
        self.tipo = TipoMaterial(
            nome="PET",
            descricao="PET para testes",
            categoria=CategoriaMaterial.PLASTICO,
        )

        self.repositorio = SimpleNamespace(
            materiais=[],
            tipos=[self.tipo],
        )

        self.servico = MaterialService(
            material_dao=MaterialDAO(self.repositorio),
            tipo_material_dao=TipoMaterialDAO(self.repositorio),
        )

    def test_listagem_nao_expoe_lista_interna(self):
        tipos = self.servico.listar_tipos()

        self.assertEqual(tipos, [self.tipo])

        tipos.clear()

        self.assertEqual(
            self.repositorio.tipos,
            [self.tipo],
        )
        self.assertEqual(
            self.servico.listar_tipos(),
            [self.tipo],
        )

    def test_busca_tipo_por_id(self):
        encontrado = self.servico.buscar_tipo(
            str(self.tipo.id)
        )

        self.assertIs(encontrado, self.tipo)

    def test_tipo_inexistente_retorna_none(self):
        encontrado = self.servico.buscar_tipo(
            "id-inexistente"
        )

        self.assertIsNone(encontrado)


if __name__ == "__main__":
    unittest.main()