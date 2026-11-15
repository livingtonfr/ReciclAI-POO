from flask import redirect, url_for, flash, session

from app import app
from app.dao.repositorio import Repositorio


@app.route('/admin/reset', methods=['POST'])
def admin_reset():
    Repositorio().resetar()
    session.clear()
    flash('Demo reiniciada. Todos os dados voltaram ao estado inicial.', 'success')
    return redirect(url_for('home'))
