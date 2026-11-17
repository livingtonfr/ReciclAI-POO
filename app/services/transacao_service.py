from uuid import uuid4

from app.model.comercial import Transacao, Certificado
from app.model.enums import StatusTransacao
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

class LoteNegociacaoNaoEncontradoError(LookupError):
    """O lote solicitado para negociação não existe."""

class CertificadoNaoEncontradoError(LookupError):
    """O certificado solicitado não existe."""

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
        certificado_dao=None,
    ):
        self._transacao_dao = transacao_dao
        self._lote_dao = lote_dao
        self._servico_precificacao = servico_precificacao
        self._certificado_dao = certificado_dao

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
            if lote.criador.id == usuario.id:
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

        if transacao.vendedor.id != usuario.id:
            raise AcessoTransacaoNegadoError(
                "A transação pertence a outro vendedor."
            )

        return transacao

    def propor(self, lote_id, usuario, valor_total):
        self._validar_comprador(usuario)

        lote = self._lote_dao.buscar_por_id(lote_id)

        if lote is None:
            raise LoteNegociacaoNaoEncontradoError(
                "Lote não encontrado."
            )

        ja_tem_proposta = any(
            transacao.comprador.id == usuario.id
            and transacao.status == StatusTransacao.PENDENTE
            for transacao in lote.transacoes
        )

        if ja_tem_proposta:
            raise ValueError(
                "Você já tem uma proposta pendente para este lote."
            )

        transacao = Transacao(
            lote,
            lote.criador,
            usuario,
            valor_total,
        )

        return self._transacao_dao.adicionar(transacao)

    def concluir(self, transacao_id, usuario):
        transacao = self.buscar_do_vendedor(
            transacao_id,
            usuario,
        )
        transacao.concluir()
        return self._transacao_dao.registrar_conclusao(transacao)

    def cancelar(self, transacao_id, usuario):
        transacao = self.buscar_do_vendedor(
            transacao_id,
            usuario,
        )
        transacao.cancelar()
        return self._transacao_dao.registrar_cancelamento(transacao)

    def _obter_certificado_dao(self):
        if self._certificado_dao is None:
            raise RuntimeError(
                "O DAO de certificados não foi configurado."
            )

        return self._certificado_dao

    def emitir_certificado(self, transacao_id, usuario):
        transacao = self.buscar_do_vendedor(
            transacao_id,
            usuario,
        )
        dao = self._obter_certificado_dao()

        codigo = f"CERT-{uuid4().hex.upper()}"
        certificado = Certificado(codigo)

        transacao.associarCertificado(certificado)
        return dao.adicionar(certificado, transacao)

    def consultar_certificado(self, certificado_id, usuario):
        certificado = (
            self._obter_certificado_dao()
            .buscar_por_id(certificado_id)
        )

        if certificado is None:
            raise CertificadoNaoEncontradoError(
                "Certificado não encontrado."
            )

        transacao = self._transacao_dao.buscar_por_certificado(
            certificado
        )

        if transacao is None:
            raise AcessoTransacaoNegadoError(
                "Certificado sem transação associada."
            )

        if (
            usuario.id != transacao.vendedor.id
            and usuario.id != transacao.comprador.id
        ):
            raise AcessoTransacaoNegadoError(
                "Somente os participantes podem consultar "
                "este certificado."
            )

        return certificado, transacao