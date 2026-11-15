from flask import render_template, request

from app import app
from app.controller.auth import login_obrigatorio
from app.dao.repositorio import Repositorio

TIPO_PONTO_LABEL = {
    'COOPERATIVA': 'Cooperativa',
    'PONTO_ENTREGA_VOLUNTARIA': 'Ponto de Entrega Voluntária',
    'ECOPONTO': 'Ecoponto',
    'OUTRO': 'Outro',
}


def buscar_tipo(tipo_id):
    for tipo in Repositorio().tipos:
        if str(tipo.id) == str(tipo_id):
            return tipo
    return None


@app.route('/pontos')
@login_obrigatorio
def pontos():
    tipo_id = request.args.get('tipo', '').strip()
    tipo_selecionado = buscar_tipo(tipo_id) if tipo_id else None

    pontos_lista = Repositorio().pontos
    if tipo_selecionado is not None:
        pontos_lista = [p for p in pontos_lista if p.aceitaMaterial(tipo_selecionado)]

    return render_template(
        'pontos_lista.html',
        pontos=pontos_lista,
        tipos=Repositorio().tipos,
        tipo_selecionado=tipo_selecionado,
        tipo_label=TIPO_PONTO_LABEL,
    )
