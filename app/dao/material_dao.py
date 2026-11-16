class MaterialDAO:
    """Consulta materiais no repositório em memória."""

    def __init__(self, repositorio):
        self._repositorio = repositorio

    def listar_por_responsavel(self, usuario):
        return [
            material
            for material in self._repositorio.materiais
            if material.responsavelAtual.id == usuario.id
        ]

    def buscar_por_id(self, material_id):
        for material in self._repositorio.materiais:
            if str(material.id) == str(material_id):
                return material

        return None

    def adicionar(self, material):
        if self.buscar_por_id(material.id) is not None:
            raise ValueError("O material já está cadastrado.")

        self._repositorio.materiais.append(material)
        return material

    def atualizar(self, material):
        existente = self.buscar_por_id(material.id)
        if existente is None:
            raise ValueError("Material não encontrado.")
        if existente is not material:
            raise ValueError("Use a instância de material do repositório em memória.")
        return existente

    def listar_disponiveis_por_responsavel(self, usuario):
        from app.model.enums import StatusMaterial

        return [
            material
            for material in self.listar_por_responsavel(usuario)
            if material.status == StatusMaterial.DISPONIVEL
        ]
