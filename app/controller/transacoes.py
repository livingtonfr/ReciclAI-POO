from functools import wraps

from flask import render_template, request, redirect, url_for, flash, abort

from app import app
from app.controller.auth import usuario_atual, login_obrigatorio
from app.controller.materiais import requer_perfil_material as requer_vendedor
from app.dao.repositorio import Repositorio
from app.model.usuario import Cooperativa, EmpresaCompradora, IndustriaTransformadora
from app.database.contexto import obter_conexao
from app.dao.lote_sqlite_dao import LoteSQLiteDAO
from app.dao.transacao_sqlite_dao import TransacaoSQLiteDAO
from app.dao.certificado_sqlite_dao import CertificadoSQLiteDAO
from app.services.transacao_service import (
    TransacaoService,
    TransacaoNaoEncontradaError,
    AcessoTransacaoNegadoError,
    LoteNegociacaoNaoEncontradoError,
    CertificadoNaoEncontradoError,
)

PERFIS_COMPRADOR = (Cooperativa, EmpresaCompradora, IndustriaTransformadora)

def obter_transacao_service():
    repositorio = Repositorio()
    conexao = obter_conexao()

    return TransacaoService(
        transacao_dao=TransacaoSQLiteDAO(conexao),
        lote_dao=LoteSQLiteDAO(conexao),
        servico_precificacao=repositorio.servico_precificacao,
        certificado_dao=CertificadoSQLiteDAO(conexao),
    )

def requer_comprador(view):
    @wraps(view)
    def decorado(*args, **kwargs):
        if not isinstance(usuario_atual(), PERFIS_COMPRADOR):
            abort(403)
        return view(*args, **kwargs)
    return decorado

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
    try:
        valor_total = float(
            request.form.get('valorTotal', '0').replace(',', '.')
        )
    except ValueError:
        flash('Informe um valor válido.', 'error')
        return redirect(url_for('mercado'))

    try:
        obter_transacao_service().propor(
            lote_id,
            usuario_atual(),
            valor_total,
        )
        flash('Proposta de compra enviada.', 'success')
    except LoteNegociacaoNaoEncontradoError:
        abort(404)
    except AcessoTransacaoNegadoError:
        abort(403)
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
    try:
        obter_transacao_service().concluir(
            transacao_id,
            usuario_atual(),
        )
        flash(
            'Transação concluída. As demais propostas '
            'pendentes deste lote foram canceladas.',
            'success',
        )
    except TransacaoNaoEncontradaError:
        abort(404)
    except AcessoTransacaoNegadoError:
        abort(403)
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('transacoes'))


@app.route('/transacoes/<transacao_id>/cancelar', methods=['POST'])
@login_obrigatorio
@requer_vendedor
def transacoes_cancelar(transacao_id):
    try:
        obter_transacao_service().cancelar(
            transacao_id,
            usuario_atual(),
        )
        flash('Proposta cancelada.', 'success')
    except TransacaoNaoEncontradaError:
        abort(404)
    except AcessoTransacaoNegadoError:
        abort(403)
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('transacoes'))


@app.route('/transacoes/<transacao_id>/certificado', methods=['POST'])
@login_obrigatorio
@requer_vendedor
def transacoes_certificado(transacao_id):
    try:
        certificado = (
            obter_transacao_service().emitir_certificado(
                transacao_id,
                usuario_atual(),
            )
        )
    except TransacaoNaoEncontradaError:
        abort(404)
    except AcessoTransacaoNegadoError:
        abort(403)
    except ValueError as erro:
        flash(str(erro), 'error')
        return redirect(url_for('transacoes'))

    flash('Certificado emitido.', 'success')
    return redirect(
        url_for(
            'certificado_detalhe',
            certificado_id=certificado.id,
        )
    )


@app.route('/certificados/<certificado_id>')
@login_obrigatorio
def certificado_detalhe(certificado_id):
    usuario = usuario_atual()

    try:
        certificado, transacao = (
            obter_transacao_service().consultar_certificado(
                certificado_id,
                usuario,
            )
        )
    except CertificadoNaoEncontradoError:
        abort(404)
    except AcessoTransacaoNegadoError:
        abort(403)

    return render_template(
        'certificado_detalhe.html',
        certificado=certificado,
        transacao=transacao,
        usuario=usuario,
    )
