from app.model.usuario import (
    Catador,
    Cooperativa,
    EmpresaCompradora,
    IndustriaTransformadora,
)


class TransacaoNaoEncontradaError(LookupError):
    """A transação solicitada não existe."""


class AcessoTransacaoNegadoError(PermissionError):
    """O usuário não pode acessar essa operação."""


class TransacaoService:
    PERFIS_COMPRADORES = (
        Cooperativa,
        EmpresaCompradora,
        IndustriaTransformadora,
    )

    PERFIS_VENDEDORES = (
        Catador,
        Cooperativa,
        EmpresaCompradora,
    )

    def __init__(
        self,
        transacao_dao,
        lote_dao,
        servico_precificacao,
    ):
        self._transacao_dao = transacao_dao
        self._lote_dao = lote_dao
        self._servico_precificacao = servico_precificacao

    def _validar_comprador(self, usuario):
        if not isinstance(usuario, self.PERFIS_COMPRADORES):
            raise AcessoTransacaoNegadoError(
                "Este perfil não pode realizar compras."
            )

    def _validar_vendedor(self, usuario):
        if not isinstance(usuario, self.PERFIS_VENDEDORES):
            raise AcessoTransacaoNegadoError(
                "Este perfil não pode gerenciar vendas."
            )

    def listar_mercado(self, usuario):
        self._validar_comprador(usuario)
        ofertas = []

        for lote in self._lote_dao.listar_disponiveis():
            if lote.criador is usuario:
                continue

            peso = (
                lote.pesoRegistrado
                if lote.pesoRegistrado is not None
                else lote.calcularPesoTotal()
            )

            cotacao = self._servico_precificacao.cotarLote(
                lote,
                15,
            )

            ofertas.append({
                "lote": lote,
                "peso": peso,
                "valor_sugerido": round(
                    cotacao.valorPorKg * peso,
                    2,
                ),
            })

        return ofertas

    def listar_propostas(self, usuario):
        self._validar_comprador(usuario)
        return self._transacao_dao.listar_por_comprador(usuario)

    def listar_vendas(self, usuario):
        self._validar_vendedor(usuario)
        return self._transacao_dao.listar_por_vendedor(usuario)

    def buscar_do_vendedor(self, transacao_id, usuario):
        self._validar_vendedor(usuario)

        transacao = self._transacao_dao.buscar_por_id(
            transacao_id
        )

        if transacao is None:
            raise TransacaoNaoEncontradaError(
                "Transação não encontrada."
            )

        if transacao.vendedor is not usuario:
            raise AcessoTransacaoNegadoError(
                "A transação pertence a outro vendedor."
            )

        return transacao