from flask import redirect, url_for, flash, session, abort

from app import app
from app.controller.auth import (
    login_obrigatorio,
    usuario_atual,
)
from app.database.contexto import obter_conexao
from app.database.seed import resetar_banco
from app.services.demo_service import (
    DemoService,
    ResetDemoNegadoError,
)


def obter_demo_service():
    return DemoService(
        reinicializar=lambda: resetar_banco(obter_conexao())
    )


@app.route('/admin/reset', methods=['POST'])
@login_obrigatorio
def admin_reset():
    # O reset apaga TODOS os dados do SQLite; só roda se o desenvolvedor
    # habilitar explicitamente (RECICLAI_PERMITIR_RESET=1) em modo debug.
    if not app.config.get('PERMITIR_RESET_DEMO'):
        flash(
            'O reset da demonstração está desabilitado para '
            'proteger os dados gravados no banco.',
            'error',
        )
        return redirect(url_for('dashboard'))

    try:
        obter_demo_service().resetar(
            usuario=usuario_atual(),
            modo_desenvolvimento=app.debug,
        )
    except ResetDemoNegadoError:
        abort(403)

    session.clear()
    flash(
        'Banco apagado e recarregado com os dados iniciais '
        'da demonstração.',
        'success',
    )
    return redirect(url_for('home'))
