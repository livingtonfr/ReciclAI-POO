from functools import wraps

from flask import render_template, request, abort

from app import app
from app.controller.auth import usuario_atual, login_obrigatorio
from app.dao.repositorio import Repositorio
from app.model.usuario import UsuarioComum
from app.services.identificacao_service import IdentificacaoService, AcessoIdentificacaoNegadoError

CATEGORIA_LABEL = {
    'PLASTICO': 'Plástico',
    'PAPEL': 'Papel',
    'VIDRO': 'Vidro',
    'METAL': 'Metal',
    'ORGANICO': 'Orgânico',
    'ELETRONICO': 'Eletrônico',
    'PERIGOSO': 'Perigoso',
    'REJEITO': 'Rejeito',
}

DICA_DESCARTE = {
    'PLASTICO': 'Lave e seque a embalagem antes de descartar. Retire tampas e rótulos quando possível.',
    'PAPEL': 'Mantenha o papel seco e sem contaminação de gordura ou alimentos.',
    'VIDRO': 'Embrulhe vidros quebrados para evitar acidentes e separe por cor quando possível.',
    'METAL': 'Enxágue latas e embalagens metálicas antes de descartar.',
}

DICA_PADRAO = 'Separe este material dos demais e procure um ponto de coleta adequado.'


def requer_usuario_comum(view):
    @wraps(view)
    def decorado(*args, **kwargs):
        if not isinstance(usuario_atual(), UsuarioComum):
            abort(403)
        return view(*args, **kwargs)
    return decorado

def obter_identificacao_service():
    return IdentificacaoService(
        Repositorio().servico_visao
    )


@app.route('/ia/identificar', methods=['GET', 'POST'])
@login_obrigatorio
@requer_usuario_comum
def ia_identificar():
    if request.method == 'POST':
        usuario = usuario_atual()
        foto = request.form.get('foto', 'foto_garrafa_pet.jpg')
        try:
            resultado = obter_identificacao_service().identificar(
                usuario,
                foto,
            )
        except AcessoIdentificacaoNegadoError:
            abort(403)
            
        categoria = resultado.tipoMaterial.categoria.name

        return render_template(
            'ia_resultado.html',
            resultado=resultado,
            categoria_label=CATEGORIA_LABEL.get(categoria, categoria.title()),
            dica=DICA_DESCARTE.get(categoria, DICA_PADRAO),
        )

    return render_template('ia_identificar.html')
