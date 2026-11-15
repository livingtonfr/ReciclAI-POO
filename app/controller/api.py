from flask import jsonify, request

from app import app
from app.controller.auth import login_obrigatorio
from app.controller.materiais import buscar_material_do_usuario
from app.dao.repositorio import Repositorio


def ponto_para_json(ponto):
    return {
        'id': str(ponto.id),
        'nome': ponto.nome,
        'endereco': ponto.endereco,
        'latitude': ponto.latitude,
        'longitude': ponto.longitude,
        'tipo': ponto.tipo.value,
        'tiposAceitos': [tipo.nome for tipo in ponto.tiposAceitos],
        'horarios': [
            {
                'diaSemana': horario.diaSemana.value,
                'horaAbertura': horario.horaAbertura.strftime('%H:%M'),
                'horaFechamento': horario.horaFechamento.strftime('%H:%M'),
            }
            for horario in ponto.horarios
        ],
    }


@app.route('/api/pontos')
def api_pontos():
    tipo_id = request.args.get('tipo', '').strip()
    pontos = Repositorio().pontos

    if tipo_id:
        tipo = next((t for t in Repositorio().tipos if str(t.id) == tipo_id), None)
        if tipo is not None:
            pontos = [p for p in pontos if p.aceitaMaterial(tipo)]

    return jsonify([ponto_para_json(ponto) for ponto in pontos])


@app.route('/api/materiais/<material_id>/historico')
@login_obrigatorio
def api_materiais_historico(material_id):
    material = buscar_material_do_usuario(material_id)

    return jsonify([
        {
            'tipo': evento.tipo.value,
            'dataEvento': evento.dataEvento.isoformat(),
            'descricao': evento.descricao,
        }
        for evento in material.obterHistorico()
    ])
