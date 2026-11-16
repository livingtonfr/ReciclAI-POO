class TransacaoDAO:
    """Consulta transações no repositório em memória."""

    def __init__(self, repositorio):
        self._repositorio = repositorio

    def buscar_por_id(self, transacao_id):
        for transacao in self._repositorio.transacoes:
            if str(transacao.id) == str(transacao_id):
                return transacao

        return None

    def listar_por_comprador(self, usuario):
        return [
            transacao
            for transacao in self._repositorio.transacoes
            if transacao.comprador is usuario
        ]

    def listar_por_vendedor(self, usuario):
        return [
            transacao
            for transacao in self._repositorio.transacoes
            if transacao.vendedor is usuario
        ]