import uuid
from functools import wraps

from flask import render_template, request, redirect, url_for, flash, abort

from app import app
from app.controller.auth import usuario_atual, login_obrigatorio
from app.controller.materiais import requer_perfil_material as requer_vendedor
from app.dao.repositorio import Repositorio
from app.model.enums import StatusLote, StatusTransacao
from app.model.usuario import Cooperativa, EmpresaCompradora, IndustriaTransformadora
from app.model.comercial import Transacao, Certificado
from app.dao.lote_dao import LoteDAO
from app.dao.transacao_dao import TransacaoDAO
from app.services.transacao_service import TransacaoService, TransacaoNaoEncontradaError, AcessoTransacaoNegadoError

PERFIS_COMPRADOR = (Cooperativa, EmpresaCompradora, IndustriaTransformadora)

def obter_transacao_service():
    repositorio = Repositorio()

    return TransacaoService(
        transacao_dao=TransacaoDAO(repositorio),
        lote_dao=LoteDAO(repositorio),
        servico_precificacao=repositorio.servico_precificacao,
    )

def requer_comprador(view):
    @wraps(view)
    def decorado(*args, **kwargs):
        if not isinstance(usuario_atual(), PERFIS_COMPRADOR):
            abort(403)
        return view(*args, **kwargs)
    return decorado


def buscar_lote(lote_id):
    for lote in Repositorio().lotes:
        if str(lote.id) == str(lote_id):
            return lote
    abort(404)


def buscar_transacao_do_vendedor(transacao_id):
    try:
        return obter_transacao_service().buscar_do_vendedor(
            transacao_id,
            usuario_atual(),
        )
    except TransacaoNaoEncontradaError:
        abort(404)
    except AcessoTransacaoNegadoError:
        abort(403)


@app.route('/lotes/<lote_id>/propor', methods=['POST'])
@login_obrigatorio
@requer_comprador
def lotes_propor(lote_id):
    usuario = usuario_atual()
    lote = buscar_lote(lote_id)

    ja_tem_proposta_pendente = any(
        t.comprador is usuario and t.status == StatusTransacao.PENDENTE
        for t in lote.transacoes
    )
    if ja_tem_proposta_pendente:
        flash('Você já tem uma proposta pendente para este lote.', 'error')
        return redirect(url_for('mercado'))

    try:
        valor_total = float(request.form.get('valorTotal', '0').replace(',', '.'))
    except ValueError:
        flash('Informe um valor válido.', 'error')
        return redirect(url_for('mercado'))

    try:
        transacao = Transacao(lote, lote.criador, usuario, valor_total)
        Repositorio().transacoes.append(transacao)
        flash('Proposta de compra enviada.', 'success')
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('mercado'))


@app.route('/mercado')
@login_obrigatorio
@requer_comprador
def mercado():
    try:
        ofertas = obter_transacao_service().listar_mercado(
            usuario_atual()
        )
    except AcessoTransacaoNegadoError:
        abort(403)

    return render_template(
        'mercado.html',
        lotes=ofertas,
    )


@app.route('/minhas-propostas')
@login_obrigatorio
@requer_comprador
def minhas_propostas():
    try:
        propostas = obter_transacao_service().listar_propostas(
            usuario_atual()
        )
    except AcessoTransacaoNegadoError:
        abort(403)

    return render_template(
        'minhas_propostas.html',
        propostas=propostas,
    )


@app.route('/transacoes')
@login_obrigatorio
@requer_vendedor
def transacoes():
    try:
        vendas = obter_transacao_service().listar_vendas(
            usuario_atual()
        )
    except AcessoTransacaoNegadoError:
        abort(403)

    return render_template(
        'transacoes_lista.html',
        transacoes=vendas,
    )


@app.route('/transacoes/<transacao_id>/concluir', methods=['POST'])
@login_obrigatorio
@requer_vendedor
def transacoes_concluir(transacao_id):
    transacao = buscar_transacao_do_vendedor(transacao_id)

    try:
        transacao.concluir()
        flash(
            'Transação concluída. As demais propostas pendentes deste lote foram canceladas.',
            'success',
        )
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('transacoes'))


@app.route('/transacoes/<transacao_id>/cancelar', methods=['POST'])
@login_obrigatorio
@requer_vendedor
def transacoes_cancelar(transacao_id):
    transacao = buscar_transacao_do_vendedor(transacao_id)

    try:
        transacao.cancelar()
        flash('Proposta cancelada.', 'success')
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('transacoes'))


@app.route('/transacoes/<transacao_id>/certificado', methods=['POST'])
@login_obrigatorio
@requer_vendedor
def transacoes_certificado(transacao_id):
    transacao = buscar_transacao_do_vendedor(transacao_id)

    try:
        codigo = f"CERT-{uuid.uuid4().hex[:8].upper()}"
        certificado = Certificado(codigo)
        transacao.associarCertificado(certificado)
        Repositorio().certificados.append(certificado)
        flash('Certificado emitido.', 'success')
        return redirect(url_for('certificado_detalhe', certificado_id=certificado.id))
    except ValueError as erro:
        flash(str(erro), 'error')
        return redirect(url_for('transacoes'))


@app.route('/certificados/<certificado_id>')
@login_obrigatorio
def certificado_detalhe(certificado_id):
    usuario = usuario_atual()

    for certificado in Repositorio().certificados:
        if str(certificado.id) == str(certificado_id):
            transacao = next(
                (t for t in Repositorio().transacoes if t.certificado is certificado),
                None,
            )

            if transacao is None or usuario not in (transacao.vendedor, transacao.comprador):
                abort(403)

            return render_template(
                'certificado_detalhe.html',
                certificado=certificado,
                transacao=transacao,
            )

    abort(404)
