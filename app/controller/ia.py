from functools import wraps

from flask import render_template, request, abort

from app import app
from app.controller.auth import usuario_atual, login_obrigatorio
from app.dao.repositorio import Repositorio
from app.model.usuario import UsuarioComum


def requer_usuario_comum(view):
    @wraps(view)
    def decorado(*args, **kwargs):
        if not isinstance(usuario_atual(), UsuarioComum):
            abort(403)
        return view(*args, **kwargs)
    return decorado


@app.route('/ia/identificar', methods=['GET', 'POST'])
@login_obrigatorio
@requer_usuario_comum
def ia_identificar():
    resultado = None

    if request.method == 'POST':
        usuario = usuario_atual()
        foto = request.form.get('foto', 'foto_simulada.jpg')
        resultado = usuario.identificarResiduo(foto, Repositorio().servico_visao)

    return render_template('ia_identificar.html', resultado=resultado)
