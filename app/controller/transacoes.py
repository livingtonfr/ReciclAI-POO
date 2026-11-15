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

PERFIS_COMPRADOR = (Cooperativa, EmpresaCompradora, IndustriaTransformadora)


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
    usuario = usuario_atual()

    for transacao in Repositorio().transacoes:
        if str(transacao.id) == str(transacao_id):
            if transacao.vendedor is not usuario:
                abort(403)
            return transacao

    abort(404)


@app.route('/mercado')
@login_obrigatorio
@requer_comprador
def mercado():
    usuario = usuario_atual()
    lotes_disponiveis = []

    for lote in Repositorio().lotes:
        if lote.status != StatusLote.DISPONIVEL or lote.criador is usuario:
            continue

        peso = lote.pesoRegistrado if lote.pesoRegistrado is not None else lote.calcularPesoTotal()
        cotacao = Repositorio().servico_precificacao.cotarLote(lote, 15)

        lotes_disponiveis.append({
            'lote': lote,
            'peso': peso,
            'valor_sugerido': round(cotacao.valorPorKg * peso, 2),
        })

    return render_template('mercado.html', lotes=lotes_disponiveis)


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


@app.route('/minhas-propostas')
@login_obrigatorio
@requer_comprador
def minhas_propostas():
    usuario = usuario_atual()
    propostas = [t for t in Repositorio().transacoes if t.comprador is usuario]
    return render_template('minhas_propostas.html', propostas=propostas)


@app.route('/transacoes')
@login_obrigatorio
@requer_vendedor
def transacoes():
    usuario = usuario_atual()
    minhas_transacoes = [t for t in Repositorio().transacoes if t.vendedor is usuario]
    return render_template('transacoes_lista.html', transacoes=minhas_transacoes)


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
