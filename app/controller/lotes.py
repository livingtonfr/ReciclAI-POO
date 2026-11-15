from flask import render_template, request, redirect, url_for, flash, abort

from app import app
from app.controller.auth import usuario_atual, login_obrigatorio
from app.controller.materiais import requer_perfil_material
from app.dao.repositorio import Repositorio
from app.model.enums import StatusMaterial


def buscar_lote_do_usuario(lote_id):
    usuario = usuario_atual()

    for lote in Repositorio().lotes:
        if str(lote.id) == str(lote_id):
            if lote.criador is not usuario:
                abort(403)
            return lote

    abort(404)


def materiais_disponiveis_do_usuario(usuario, excluir=None):
    return [
        material for material in Repositorio().materiais
        if material.responsavelAtual is usuario
        and material.status == StatusMaterial.DISPONIVEL
        and material is not excluir
    ]


@app.route('/lotes')
@login_obrigatorio
@requer_perfil_material
def lotes():
    usuario = usuario_atual()
    meus_lotes = [lote for lote in Repositorio().lotes if lote.criador is usuario]
    return render_template('lotes_lista.html', lotes=meus_lotes)


@app.route('/lotes/novo', methods=['GET', 'POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_novo():
    usuario = usuario_atual()
    materiais_disponiveis = materiais_disponiveis_do_usuario(usuario)

    if request.method == 'POST':
        material_id = request.form.get('material_id')
        material = next(
            (m for m in materiais_disponiveis if str(m.id) == material_id),
            None,
        )

        if material is None:
            flash('Selecione um material disponível para iniciar o lote.', 'error')
            return render_template('lotes_novo.html', materiais=materiais_disponiveis)

        try:
            lote = usuario.criarLote(material)
        except ValueError as erro:
            flash(str(erro), 'error')
            return render_template('lotes_novo.html', materiais=materiais_disponiveis)

        Repositorio().lotes.append(lote)
        flash('Lote criado com sucesso.', 'success')
        return redirect(url_for('lotes_detalhe', lote_id=lote.id))

    return render_template('lotes_novo.html', materiais=materiais_disponiveis)


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
    usuario = usuario_atual()
    lote = buscar_lote_do_usuario(lote_id)
    material_id = request.form.get('material_id')

    material = next(
        (m for m in materiais_disponiveis_do_usuario(usuario) if str(m.id) == material_id),
        None,
    )

    if material is None:
        flash('Selecione um material disponível.', 'error')
        return redirect(url_for('lotes_detalhe', lote_id=lote.id))

    try:
        lote.adicionarMaterial(material)
        flash('Material adicionado ao lote.', 'success')
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('lotes_detalhe', lote_id=lote.id))


@app.route('/lotes/<lote_id>/remover', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_remover(lote_id):
    lote = buscar_lote_do_usuario(lote_id)
    material_id = request.form.get('material_id')

    material = next((m for m in lote.materiais if str(m.id) == material_id), None)

    if material is None:
        flash('Material não encontrado neste lote.', 'error')
        return redirect(url_for('lotes_detalhe', lote_id=lote.id))

    try:
        lote.removerMaterial(material)
        flash('Material removido do lote.', 'success')
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('lotes_detalhe', lote_id=lote.id))


@app.route('/lotes/<lote_id>/pesagem', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_pesagem(lote_id):
    lote = buscar_lote_do_usuario(lote_id)

    try:
        peso = float(request.form.get('peso', '0').replace(',', '.'))
    except ValueError:
        flash('Informe um número válido.', 'error')
        return redirect(url_for('lotes_detalhe', lote_id=lote.id))

    try:
        lote.registrarPesagem(peso)
        flash('Pesagem registrada.', 'success')
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('lotes_detalhe', lote_id=lote.id))


@app.route('/lotes/<lote_id>/disponibilizar', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_disponibilizar(lote_id):
    lote = buscar_lote_do_usuario(lote_id)

    try:
        lote.disponibilizar()
        flash('Lote disponibilizado para negociação.', 'success')
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('lotes_detalhe', lote_id=lote.id))


@app.route('/lotes/<lote_id>/cancelar', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_cancelar(lote_id):
    lote = buscar_lote_do_usuario(lote_id)

    try:
        lote.cancelar()
        flash('Lote cancelado.', 'success')
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('lotes_detalhe', lote_id=lote.id))


@app.route('/lotes/<lote_id>/cotar', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def lotes_cotar(lote_id):
    usuario = usuario_atual()
    lote = buscar_lote_do_usuario(lote_id)

    try:
        horizonte_dias = int(request.form.get('horizonteDias', '15'))
    except ValueError:
        flash('Informe um número válido de dias.', 'error')
        return redirect(url_for('lotes_detalhe', lote_id=lote.id))

    try:
        cotacao = usuario.solicitarPrecificacaoLote(
            lote,
            horizonte_dias,
            Repositorio().servico_precificacao,
        )
        peso = lote.pesoRegistrado if lote.pesoRegistrado is not None else lote.calcularPesoTotal()
        total = cotacao.valorPorKg * peso
        flash(
            f'Cotação: R$ {cotacao.valorPorKg:.2f}/kg por {cotacao.horizonteDias} dias '
            f'(total estimado: R$ {total:.2f}).',
            'success',
        )
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('lotes_detalhe', lote_id=lote.id))
