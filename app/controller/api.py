from flask import jsonify, request, abort

from app import app
from app.controller.auth import login_obrigatorio, usuario_atual
from app.dao.repositorio import Repositorio
from app.database.contexto import obter_conexao
from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.dao.transacao_sqlite_dao import TransacaoSQLiteDAO
from app.dao.ponto_coleta_dao import PontoColetaDAO
from app.dao.tipo_material_dao import TipoMaterialDAO
from app.services.ponto_coleta_service import PontoColetaService
from app.services.rastreabilidade_service import (
    RastreabilidadeService,
)
from app.services.material_service import (
    MaterialNaoEncontradoError,
    AcessoMaterialNegadoError,
)


def obter_ponto_coleta_service_api():
    repositorio = Repositorio()

    return PontoColetaService(
        PontoColetaDAO(repositorio),
        TipoMaterialDAO(repositorio),
    )


def obter_rastreabilidade_service():
    conexao = obter_conexao()

    return RastreabilidadeService(
        MaterialSQLiteDAO(conexao),
        TransacaoSQLiteDAO(conexao),
    )


def ponto_para_json(ponto):
    return {
        'id': str(ponto.id),
        'nome': ponto.nome,
        'endereco': ponto.endereco,
        'latitude': ponto.latitude,
        'longitude': ponto.longitude,
        'tipo': ponto.tipo.value,
        'tiposAceitos': [
            tipo.nome for tipo in ponto.tiposAceitos
        ],
        'horarios': [
            {
                'diaSemana': horario.diaSemana.value,
                'horaAbertura': (
                    horario.horaAbertura.strftime('%H:%M')
                ),
                'horaFechamento': (
                    horario.horaFechamento.strftime('%H:%M')
                ),
            }
            for horario in ponto.horarios
        ],
    }


@app.route('/api/pontos')
def api_pontos():
    tipo_id = request.args.get('tipo', '').strip()

    pontos, _ = obter_ponto_coleta_service_api().consultar(
        tipo_id
    )

    return jsonify([
        ponto_para_json(ponto)
        for ponto in pontos
    ])


@app.route('/api/materiais/<material_id>/historico')
@login_obrigatorio
def api_materiais_historico(material_id):
    try:
        historico = (
            obter_rastreabilidade_service().consultar_historico(
                material_id,
                usuario_atual(),
            )
        )
    except MaterialNaoEncontradoError:
        abort(404)
    except AcessoMaterialNegadoError:
        abort(403)

    return jsonify([
        {
            'tipo': evento.tipo.value,
            'dataEvento': evento.dataEvento.isoformat(),
            'descricao': evento.descricao,
        }
        for evento in historico
    ])