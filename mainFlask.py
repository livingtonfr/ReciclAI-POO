from app import app

if __name__ == '__main__':
    # use_reloader=False: o reloader reinicia o processo a cada arquivo salvo,
    # e isso zera o Repositorio em memória no meio da demo. debug=True fica
    # ligado porque /admin/reset só funciona com app.debug ativo.
    app.run(debug=True, use_reloader=False)
