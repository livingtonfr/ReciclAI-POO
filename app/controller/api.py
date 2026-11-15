from flask import jsonify, request, abort

from app import app
from app.controller.auth import login_obrigatorio, usuario_atual
from app.dao.repositorio import Repositorio
from app.model.enums import StatusTransacao


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


def usuario_pode_ver_historico(usuario, material):
    if material.responsavelAtual is usuario:
        return True

    for transacao in Repositorio().transacoes:
        if transacao.status != StatusTransacao.CONCLUIDA:
            continue
        if material not in transacao.lote.materiais:
            continue
        if usuario is transacao.vendedor or usuario is transacao.comprador:
            return True

    return False


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
    usuario = usuario_atual()
    material = Repositorio().buscarMaterialPorId(material_id)

    if material is None:
        abort(404)

    if not usuario_pode_ver_historico(usuario, material):
        abort(403)

    return jsonify([
        {
            'tipo': evento.tipo.value,
            'dataEvento': evento.dataEvento.isoformat(),
            'descricao': evento.descricao,
        }
        for evento in material.obterHistorico()
    ])
