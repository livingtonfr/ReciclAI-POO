from flask import render_template, request

from app import app
from app.controller.auth import login_obrigatorio
from app.dao.repositorio import Repositorio
from app.dao.ponto_coleta_dao import PontoColetaDAO
from app.dao.tipo_material_dao import TipoMaterialDAO
from app.services.ponto_coleta_service import PontoColetaService


TIPO_PONTO_LABEL = {
    'COOPERATIVA': 'Cooperativa',
    'PONTO_ENTREGA_VOLUNTARIA': 'Ponto de Entrega Voluntária',
    'ECOPONTO': 'Ecoponto',
    'OUTRO': 'Outro',
}


def obter_ponto_coleta_service():
    repositorio = Repositorio()

    return PontoColetaService(
        ponto_coleta_dao=PontoColetaDAO(repositorio),
        tipo_material_dao=TipoMaterialDAO(repositorio),
    )


@app.route('/pontos')
@login_obrigatorio
def pontos():
    tipo_id = request.args.get('tipo', '').strip()
    servico = obter_ponto_coleta_service()

    pontos_lista, tipo_selecionado = servico.consultar(
        tipo_id
    )

    return render_template(
        'pontos_lista.html',
        pontos=pontos_lista,
        tipos=servico.listar_tipos(),
        tipo_selecionado=tipo_selecionado,
        tipo_label=TIPO_PONTO_LABEL,
    )