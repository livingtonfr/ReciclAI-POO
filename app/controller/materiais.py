from functools import wraps

from flask import render_template, request, redirect, url_for, flash, abort

from app import app
from app.controller.auth import usuario_atual, login_obrigatorio
from app.dao.repositorio import Repositorio
from app.model.enums import CondicaoMaterial
from app.model.usuario import Catador, Cooperativa, EmpresaCompradora

PERFIS_MATERIAL = (Catador, Cooperativa, EmpresaCompradora)


def requer_perfil_material(view):
    @wraps(view)
    def decorado(*args, **kwargs):
        if not isinstance(usuario_atual(), PERFIS_MATERIAL):
            abort(403)
        return view(*args, **kwargs)
    return decorado


def requer_catador(view):
    @wraps(view)
    def decorado(*args, **kwargs):
        if not isinstance(usuario_atual(), Catador):
            abort(403)
        return view(*args, **kwargs)
    return decorado


def buscar_material_do_usuario(material_id):
    usuario = usuario_atual()

    for material in Repositorio().materiais:
        if str(material.id) == str(material_id):
            if material.responsavelAtual is not usuario:
                abort(403)
            return material

    abort(404)


def buscar_tipo(tipo_id):
    for tipo in Repositorio().tipos:
        if str(tipo.id) == str(tipo_id):
            return tipo
    return None


@app.route('/materiais')
@login_obrigatorio
@requer_perfil_material
def materiais():
    usuario = usuario_atual()
    meus_materiais = [
        material for material in Repositorio().materiais
        if material.responsavelAtual is usuario
    ]
    return render_template(
        'materiais_lista.html',
        materiais=meus_materiais,
        usuario_e_catador=isinstance(usuario, Catador),
    )


@app.route('/materiais/novo', methods=['GET', 'POST'])
@login_obrigatorio
@requer_catador
def materiais_novo():
    usuario = usuario_atual()
    tipos = Repositorio().tipos
    condicoes = list(CondicaoMaterial)

    if request.method == 'POST':
        tipo = buscar_tipo(request.form.get('tipo_id'))
        observacoes = request.form.get('observacoes', '').strip() or None

        if tipo is None:
            flash('Selecione um tipo de material válido.', 'error')
            return render_template('materiais_novo.html', tipos=tipos, condicoes=condicoes)

        try:
            peso_kg = float(request.form.get('pesoKg', '0').replace(',', '.'))
            condicao = CondicaoMaterial[request.form.get('condicaoDeclarada')]
            material = usuario.registrarMaterial(tipo, peso_kg, condicao, observacoes)
        except (ValueError, KeyError) as erro:
            flash(f'Não foi possível registrar o material: {erro}', 'error')
            return render_template('materiais_novo.html', tipos=tipos, condicoes=condicoes)

        Repositorio().materiais.append(material)
        flash('Material registrado com sucesso.', 'success')
        return redirect(url_for('materiais_detalhe', material_id=material.id))

    return render_template('materiais_novo.html', tipos=tipos, condicoes=condicoes)


@app.route('/materiais/<material_id>')
@login_obrigatorio
@requer_perfil_material
def materiais_detalhe(material_id):
    material = buscar_material_do_usuario(material_id)
    return render_template(
        'materiais_detalhe.html',
        material=material,
        historico=material.obterHistorico(),
        avaliacoes=material.obterAvaliacoes(),
    )


@app.route('/materiais/<material_id>/disponibilizar', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def materiais_disponibilizar(material_id):
    material = buscar_material_do_usuario(material_id)

    try:
        material.disponibilizar()
        flash('Material disponibilizado para negociação.', 'success')
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('materiais_detalhe', material_id=material.id))


@app.route('/materiais/<material_id>/avaliar', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def materiais_avaliar(material_id):
    material = buscar_material_do_usuario(material_id)
    foto = request.form.get('foto', 'foto_simulada.jpg')

    avaliacao = Repositorio().servico_visao.avaliarMaterial(material, foto)
    flash(
        f'IA avaliou o material como {avaliacao.condicaoDetectada.value} '
        f'(confiança {avaliacao.confianca:.0%}). A condição declarada não foi alterada.',
        'info',
    )

    return redirect(url_for('materiais_detalhe', material_id=material.id))


@app.route('/materiais/<material_id>/cotar', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def materiais_cotar(material_id):
    usuario = usuario_atual()
    material = buscar_material_do_usuario(material_id)

    try:
        horizonte_dias = int(request.form.get('horizonteDias', '15'))
        cotacao = usuario.solicitarPrecificacaoMaterial(
            material,
            horizonte_dias,
            Repositorio().servico_precificacao,
        )
        total = cotacao.valorPorKg * material.pesoKg
        flash(
            f'Cotação: R$ {cotacao.valorPorKg:.2f}/kg por {cotacao.horizonteDias} dias '
            f'(total estimado: R$ {total:.2f}).',
            'success',
        )
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('materiais_detalhe', material_id=material.id))
