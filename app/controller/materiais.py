from functools import wraps

from flask import render_template, request, redirect, url_for, flash, abort

from app import app
from app.controller.auth import usuario_atual, login_obrigatorio
from app.dao.repositorio import Repositorio
from app.model.enums import CondicaoMaterial
from app.model.usuario import Catador, Cooperativa, EmpresaCompradora, IndustriaTransformadora
from app.dao.material_dao import MaterialDAO
from app.services.material_service import MaterialService, MaterialNaoEncontradoError, AcessoMaterialNegadoError
from app.dao.tipo_material_dao import TipoMaterialDAO

# Quem opera materiais (registra, disponibiliza, avalia, cota): só quem tem
# esses métodos no UML. A Indústria NÃO tem solicitarPrecificacaoMaterial,
# por isso fica de fora daqui (ela só recebe material por compra).
PERFIS_MATERIAL = (Catador, Cooperativa, EmpresaCompradora)

# Quem pode ver a lista/detalhe de materiais que possui, incluindo a
# Indústria (ela só visualiza o que comprou, sem nenhuma ação).
PERFIS_TITULARES_MATERIAL = PERFIS_MATERIAL + (IndustriaTransformadora,)

def obter_material_service():
    repositorio = Repositorio()

    return MaterialService(
        material_dao=MaterialDAO(repositorio),
        tipo_material_dao=TipoMaterialDAO(repositorio),
    )

def requer_perfil_material(view):
    @wraps(view)
    def decorado(*args, **kwargs):
        if not isinstance(usuario_atual(), PERFIS_MATERIAL):
            abort(403)
        return view(*args, **kwargs)
    return decorado

def requer_titular_material(view):
    @wraps(view)
    def decorado(*args, **kwargs):
        if not isinstance(usuario_atual(), PERFIS_TITULARES_MATERIAL):
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
    servico = obter_material_service()

    try:
        return servico.buscar_do_usuario(
            material_id,
            usuario_atual(),
        )
    except MaterialNaoEncontradoError:
        abort(404)
    except AcessoMaterialNegadoError:
        abort(403)

def buscar_tipo(tipo_id):
    return obter_material_service().buscar_tipo(tipo_id)

@app.route('/materiais')
@login_obrigatorio
@requer_titular_material
def materiais():
    usuario = usuario_atual()
    servico = obter_material_service()

    try:
        meus_materiais = servico.listar_do_usuario(usuario)
    except AcessoMaterialNegadoError:
        abort(403)

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
    tipos = obter_material_service().listar_tipos()
    condicoes = list(CondicaoMaterial)

    if request.method == 'POST':
        tipo = buscar_tipo(request.form.get('tipo_id'))
        observacoes = request.form.get('observacoes', '').strip() or None

        if tipo is None:
            flash('Selecione um tipo de material válido.', 'error')
            return render_template('materiais_novo.html', tipos=tipos, condicoes=condicoes)

        try:
            peso_kg = float(request.form.get('pesoKg', '0').replace(',', '.'))
        except ValueError:
            flash('Informe um peso válido.', 'error')
            return render_template('materiais_novo.html', tipos=tipos, condicoes=condicoes)

        try:
            condicao = CondicaoMaterial[request.form.get('condicaoDeclarada')]
        except KeyError:
            flash('Selecione uma condição válida.', 'error')
            return render_template('materiais_novo.html', tipos=tipos, condicoes=condicoes)

        try:
            material = obter_material_service().registrar(
                usuario,
                tipo,
                peso_kg,
                condicao,
                observacoes,
            )
        except AcessoMaterialNegadoError:
            abort(403)
        except ValueError as erro:
            flash(str(erro), 'error')
            return render_template(
                'materiais_novo.html',
                tipos=tipos,
                condicoes=condicoes,
            )

        flash('Material registrado com sucesso.', 'success')
        return redirect(url_for('materiais_detalhe', material_id=material.id))

    return render_template('materiais_novo.html', tipos=tipos, condicoes=condicoes)


@app.route('/materiais/<material_id>')
@login_obrigatorio
@requer_titular_material
def materiais_detalhe(material_id):
    usuario = usuario_atual()
    material = buscar_material_do_usuario(material_id)
    return render_template(
        'materiais_detalhe.html',
        material=material,
        historico=material.obterHistorico(),
        avaliacoes=material.obterAvaliacoes(),
        pode_operar=isinstance(usuario, PERFIS_MATERIAL),
    )


@app.route('/materiais/<material_id>/disponibilizar', methods=['POST'])
@login_obrigatorio
@requer_perfil_material
def materiais_disponibilizar(material_id):
    try:
        obter_material_service().disponibilizar(
            material_id,
            usuario_atual(),
        )
        flash(
            'Material disponibilizado para negociação.',
            'success',
        )
    except MaterialNaoEncontradoError:
        abort(404)
    except AcessoMaterialNegadoError:
        abort(403)
    except ValueError as erro:
        flash(str(erro), 'error')

    return redirect(url_for('materiais_detalhe', material_id=material_id))


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
    except ValueError:
        flash('Informe um número válido de dias.', 'error')
        return redirect(url_for('materiais_detalhe', material_id=material.id))

    try:
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
