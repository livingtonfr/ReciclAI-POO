from flask import render_template

from app import app


@app.errorhandler(404)
def erro_404(erro):
    return render_template(
        'erro.html',
        codigo=404,
        titulo='Página não encontrada',
        mensagem='O endereço que você tentou acessar não existe ou foi movido.',
    ), 404


@app.errorhandler(403)
def erro_403(erro):
    return render_template(
        'erro.html',
        codigo=403,
        titulo='Acesso não permitido',
        mensagem='Seu perfil não tem permissão para acessar esta página.',
    ), 403


@app.errorhandler(405)
def erro_405(erro):
    return render_template(
        'erro.html',
        codigo=405,
        titulo='Operação não permitida',
        mensagem='Essa ação não pode ser feita por aqui.',
    ), 405
