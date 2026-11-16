class PontoColetaService:
    """Coordena consultas e filtros de pontos de coleta."""

    def __init__(self, ponto_coleta_dao, tipo_material_dao):
        self._ponto_coleta_dao = ponto_coleta_dao
        self._tipo_material_dao = tipo_material_dao

    def listar_tipos(self):
        return self._tipo_material_dao.listar()

    def consultar(self, tipo_id=None):
        tipo_selecionado = None

        if tipo_id:
            tipo_selecionado = (
                self._tipo_material_dao.buscar_por_id(tipo_id)
            )

        pontos = self._ponto_coleta_dao.listar()

        if tipo_selecionado is not None:
            pontos = [
                ponto
                for ponto in pontos
                if ponto.aceitaMaterial(tipo_selecionado)
            ]

        return pontos, tipo_selecionado