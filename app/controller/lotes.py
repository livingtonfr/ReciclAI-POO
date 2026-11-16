from flask import render_template, request, redirect, url_for, flash, abort

from app import app
from app.controller.auth import usuario_atual, login_obrigatorio
from app.controller.materiais import requer_perfil_material
from app.dao.repositorio import Repositorio
from app.database.contexto import obter_conexao
from app.dao.lote_sqlite_dao import LoteSQLiteDAO
from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.services.lote_service import LoteService, LoteNaoEncontradoError, AcessoLoteNegadoError

def obter_lote_service():
    repositorio = Repositorio()
    conexao = obter_conexao()

    return LoteService(
        lote_dao=LoteSQLiteDAO(conexao),
        material_dao=MaterialSQLiteDAO(conexao),
        servico_precificacao=repositorio.servico_precificacao,
    )

def buscar_lote_do_usuario(lote_id):
    try:
        return obter_lote_service().buscar_do_usuario(
            lote_id,
            usuario_atual(),
        )
    except LoteNaoEncontradoError:
        abort(404)
    except AcessoLoteNegadoError:
        abort(403)

def materiais_disponiveis_do_usuario(usuario, excluir=None):
    try:
        return obter_lote_service().listar_materiais_disponiveis(
            usuario,
            excluir=excluir,
        )
    except AcessoLoteNegadoError:
        abort(403)


@app.route('/lotes')
@login_obrigatorio
@requer_perfil_material
def lotes():
    try:
        meus_lotes = obter_lote_service().listar_do_usuario(
            usuario_atual()
        )
    except AcessoLoteNegadoError:
        abort(403)

    return render_template(
        'lotes_lista.html',
        lotes=meus_lotes,
    )

@app.route('/lotes/novo', methods=['GET', 'POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_novo():
    usuario = usuario_atual()
    servico = obter_lote_service()

    if request.method == 'POST':
        try:
            lote = servico.criar(
                usuario,
                request.form.get('material_id'),
            )
        except AcessoLoteNegadoError:
            abort(403)
        except ValueError as erro:
            flash(str(erro), 'error')
        else:
            flash('Lote criado com sucesso.', 'success')
            return redirect(
                url_for(
                    'lotes_detalhe',
                    lote_id=lote.id,
                )
            )

    materiais_disponiveis = materiais_disponiveis_do_usuario(
        usuario
    )

    return render_template(
        'lotes_novo.html',
        materiais=materiais_disponiveis,
    )

@app.route('/lotes/<lote_id>')
@login_obrigatorio
@requer_perfil_material
def lotes_detalhe(lote_id):
    usuario = usuario_atual()
    lote = buscar_lote_do_usuario(lote_id)
    materiais_para_adicionar = materiais_disponiveis_do_usuario(usuario)

    return render_template(
        'lotes_detalhe.html',
        lote=lote,
        materiais_para_adicionar=materiais_para_adicionar,
    )


@app.route('/lotes/<lote_id>/adicionar', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_adicionar(lote_id):
    try:
        obter_lote_service().adicionar_material(
            lote_id,
            request.form.get('material_id'),
            usuario_atual(),
        )
        flash('Material adicionado ao lote.', 'success')
    except LoteNaoEncontradoError:
        abort(404)
    except AcessoLoteNegadoError:
        abort(403)
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(
        url_for(
            'lotes_detalhe',
            lote_id=lote_id,
        )
    )


@app.route('/lotes/<lote_id>/remover', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_remover(lote_id):
    try:
        obter_lote_service().remover_material(
            lote_id,
            request.form.get('material_id'),
            usuario_atual(),
        )
        flash('Material removido do lote.', 'success')
    except LoteNaoEncontradoError:
        abort(404)
    except AcessoLoteNegadoError:
        abort(403)
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(
        url_for(
            'lotes_detalhe',
            lote_id=lote_id,
        )
    )


@app.route('/lotes/<lote_id>/pesagem', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_pesagem(lote_id):
    # Confere o acesso antes de processar o formulário.
    buscar_lote_do_usuario(lote_id)

    try:
        peso = float(
            request.form.get('peso', '0').replace(',', '.')
        )
    except ValueError:
        flash('Informe um número válido.', 'error')
        return redirect(
            url_for('lotes_detalhe', lote_id=lote_id)
        )

    try:
        obter_lote_service().registrar_pesagem(
            lote_id,
            usuario_atual(),
            peso,
        )
        flash('Pesagem registrada.', 'success')
    except LoteNaoEncontradoError:
        abort(404)
    except AcessoLoteNegadoError:
        abort(403)
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(
        url_for('lotes_detalhe', lote_id=lote_id)
    )


@app.route('/lotes/<lote_id>/disponibilizar', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_disponibilizar(lote_id):
    try:
        obter_lote_service().disponibilizar(
            lote_id,
            usuario_atual(),
        )
        flash(
            'Lote disponibilizado para negociação.',
            'success',
        )
    except LoteNaoEncontradoError:
        abort(404)
    except AcessoLoteNegadoError:
        abort(403)
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(
        url_for('lotes_detalhe', lote_id=lote_id)
    )


@app.route('/lotes/<lote_id>/cancelar', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_cancelar(lote_id):
    try:
        obter_lote_service().cancelar(
            lote_id,
            usuario_atual(),
        )
        flash('Lote cancelado.', 'success')
    except LoteNaoEncontradoError:
        abort(404)
    except AcessoLoteNegadoError:
        abort(403)
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(
        url_for('lotes_detalhe', lote_id=lote_id)
    )

@app.route('/lotes/<lote_id>/cotar', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_cotar(lote_id):
    usuario = usuario_atual()
    lote = buscar_lote_do_usuario(lote_id)

    try:
        horizonte_dias = int(
            request.form.get('horizonteDias', '15')
        )
    except ValueError:
        flash('Informe um número válido de dias.', 'error')
        return redirect(
            url_for('lotes_detalhe', lote_id=lote_id)
        )

    try:
        cotacao = obter_lote_service().cotar(
            lote_id,
            usuario,
            horizonte_dias,
        )

        peso = (
            lote.pesoRegistrado
            if lote.pesoRegistrado is not None
            else lote.calcularPesoTotal()
        )
        total = cotacao.valorPorKg * peso

        flash(
            f'Cotação: R$ {cotacao.valorPorKg:.2f}/kg '
            f'por {cotacao.horizonteDias} dias '
            f'(total estimado: R$ {total:.2f}).',
            'success',
        )
    except LoteNaoEncontradoError:
        abort(404)
    except AcessoLoteNegadoError:
        abort(403)
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(
        url_for('lotes_detalhe', lote_id=lote_id)
    )
