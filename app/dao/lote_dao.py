class LoteDAO:
    """Consulta lotes no repositório em memória."""

    def __init__(self, repositorio):
        self._repositorio = repositorio

    def listar_por_criador(self, usuario):
        return [
            lote
            for lote in self._repositorio.lotes
            if lote.criador is usuario
        ]

    def buscar_por_id(self, lote_id):
        for lote in self._repositorio.lotes:
            if str(lote.id) == str(lote_id):
                return lote

        return None