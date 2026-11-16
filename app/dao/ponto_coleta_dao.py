class PontoColetaDAO:
    """Consulta pontos de coleta no repositório em memória."""

    def __init__(self, repositorio):
        self._repositorio = repositorio

    def listar(self):
        return list(self._repositorio.pontos)