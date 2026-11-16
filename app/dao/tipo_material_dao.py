class TipoMaterialDAO:
    """Consulta os tipos de material disponíveis no repositório."""

    def __init__(self, repositorio):
        self._repositorio = repositorio

    def listar(self):
        return list(self._repositorio.tipos)

    def buscar_por_id(self, tipo_id):
        for tipo in self._repositorio.tipos:
            if str(tipo.id) == str(tipo_id):
                return tipo

        return None