from app.model.enums import StatusLote

class LoteDAO:
    """Consulta lotes no repositório em memória."""

    def __init__(self, repositorio):
        self._repositorio = repositorio

    def listar_por_criador(self, usuario):
        return [
            lote
            for lote in self._repositorio.lotes
            if lote.criador.id == usuario.id
        ]

    def buscar_por_id(self, lote_id):
        for lote in self._repositorio.lotes:
            if str(lote.id) == str(lote_id):
                return lote

        return None

    def adicionar(self, lote):
        if self.buscar_por_id(lote.id) is not None:
            raise ValueError("O lote já está cadastrado.")

        self._repositorio.lotes.append(lote)
        return lote

    def listar_disponiveis(self):
        return [
            lote
            for lote in self._repositorio.lotes
            if lote.status == StatusLote.DISPONIVEL
        ]

    
    def adicionar_material(self, lote_id, material_id):
        from app.dao.material_dao import MaterialDAO

        lote = self.buscar_por_id(lote_id)
        if lote is None:
            raise ValueError("Lote não encontrado.")

        material = MaterialDAO(self._repositorio).buscar_por_id(material_id)
        if material is None:
            raise ValueError("Material não encontrado.")

        lote.adicionarMaterial(material)
        return lote

    def remover_material(self, lote_id, material_id):
        lote = self.buscar_por_id(lote_id)
        if lote is None:
            raise ValueError("Lote não encontrado.")

        material = next(
            (m for m in lote.materiais if str(m.id) == str(material_id)),
            None,
        )
        if material is None:
            raise ValueError("Material não encontrado neste lote.")

        lote.removerMaterial(material)
        return lote
