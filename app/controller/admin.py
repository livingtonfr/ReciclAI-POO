from flask import redirect, url_for, flash, session, abort

from app import app
from app.controller.auth import (
    login_obrigatorio,
    usuario_atual,
)
from app.dao.repositorio import Repositorio
from app.services.demo_service import (
    DemoService,
    ResetDemoNegadoError,
)


def obter_demo_service():
    return DemoService(
        reinicializar=Repositorio().resetar
    )


@app.route('/admin/reset', methods=['POST'])
@login_obrigatorio
def admin_reset():
    try:
        obter_demo_service().resetar(
            usuario=usuario_atual(),
            modo_desenvolvimento=app.debug,
        )
    except ResetDemoNegadoError:
        abort(403)

    session.clear()
    flash(
        'Demo reiniciada. Todos os dados voltaram '
        'ao estado inicial.',
        'success',
    )
    return redirect(url_for('home'))