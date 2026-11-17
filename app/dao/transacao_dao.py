from app.model.enums import StatusTransacao

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

    def adicionar(self, transacao):
        if self.buscar_por_id(transacao.id) is not None:
            raise ValueError("A transação já está cadastrada.")

        self._repositorio.transacoes.append(transacao)
        return transacao

    def buscar_por_certificado(self, certificado):
        for transacao in self._repositorio.transacoes:
            if transacao.certificado is certificado:
                return transacao

        return None

    def listar_concluidas_por_material(self, material):
        return [
            transacao
            for transacao in self._repositorio.transacoes
            if transacao.status == StatusTransacao.CONCLUIDA
            and material in transacao.lote.materiais
        ]

    def registrar_conclusao(self, transacao):
        """Em memória, o próprio modelo já guarda o resultado."""
        return transacao

    def registrar_cancelamento(self, transacao):
        """Em memória, o próprio modelo já guarda o resultado."""
        return transacao
