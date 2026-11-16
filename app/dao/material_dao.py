class MaterialDAO:
    """Consulta materiais no repositório em memória."""

    def __init__(self, repositorio):
        self._repositorio = repositorio

    def listar_por_responsavel(self, usuario):
        return [
            material
            for material in self._repositorio.materiais
            if material.responsavelAtual is usuario
        ]

    def buscar_por_id(self, material_id):
        for material in self._repositorio.materiais:
            if str(material.id) == str(material_id):
                return material

        return None