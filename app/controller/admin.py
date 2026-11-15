from flask import redirect, url_for, flash, session, abort

from app import app
from app.controller.auth import login_obrigatorio
from app.dao.repositorio import Repositorio


@app.route('/admin/reset', methods=['POST'])
@login_obrigatorio
def admin_reset():
    if not app.debug:
        abort(403)

    Repositorio().resetar()
    session.clear()
    flash('Demo reiniciada. Todos os dados voltaram ao estado inicial.', 'success')
    return redirect(url_for('home'))
