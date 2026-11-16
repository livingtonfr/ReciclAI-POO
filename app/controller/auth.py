from functools import wraps

from flask import render_template, request, redirect, url_for, flash, abort, session

from app import app
from app.dao.repositorio import Repositorio
from app.model.usuario import (
    Catador,
    Cooperativa,
    EmpresaCompradora,
    IndustriaTransformadora,
    UsuarioComum,
)
from app.dao.usuario_dao import UsuarioDAO
from app.services.usuario_service import UsuarioService, CredenciaisInvalidasError

# Perfis exibidos na seleção de cadastro (um para cada subclasse concreta de Usuario).
# "chave" é usada na URL e no nome da classe CSS que define a cor do card;
# "documento" indica o campo extra exigido no formulário (None = nenhum).
PERFIS = [
    {'chave': 'comum', 'nome': 'Usuário Comum', 'icone': '👤',
     'descricao': 'Descarte correto e informação', 'selo': 'Gratuito',
     'classe': UsuarioComum, 'documento': None},
    {'chave': 'catador', 'nome': 'Catador', 'icone': '♻️',
     'descricao': 'Vender material com melhor preço', 'selo': 'Gratuito',
     'classe': Catador, 'documento': 'cpf'},
    {'chave': 'cooperativa', 'nome': 'Cooperativa', 'icone': '🏢',
     'descricao': 'Gestão, precificação e certificação', 'selo': 'Premium',
     'classe': Cooperativa, 'documento': 'cnpj'},
    {'chave': 'empresa', 'nome': 'Empresa Compradora', 'icone': '🏭',
     'descricao': 'Fornecimento confiável e rastreável', 'selo': 'Premium',
     'classe': EmpresaCompradora, 'documento': 'cnpj'},
    {'chave': 'industria', 'nome': 'Indústria', 'icone': '⚙️',
     'descricao': 'Insumo reciclado com rastreabilidade', 'selo': 'Premium',
     'classe': IndustriaTransformadora, 'documento': 'cnpj'},
]

PERFIS_POR_CHAVE = {p['chave']: p for p in PERFIS}

# Menu do /dashboard selecionado conforme a classe do usuário.
# UsuarioComum não usa esse menu: tem a tela "Início" própria (ações rápidas).
# Itens sem "endpoint" ainda não têm rota (entram nas próximas fases) e
# aparecem só com o rótulo e a fase em que a função é ativada.
MENU_POR_PERFIL = [
    (Catador, [
        {'rotulo': 'Meus materiais', 'endpoint': 'materiais', 'fase': None},
        {'rotulo': 'Meus lotes', 'endpoint': 'lotes', 'fase': None},
        {'rotulo': 'Minhas transações (venda)', 'endpoint': 'transacoes', 'fase': None},
        {'rotulo': 'Pontos de coleta', 'endpoint': 'pontos', 'fase': None},
    ]),
    (Cooperativa, [
        {'rotulo': 'Meus materiais', 'endpoint': 'materiais', 'fase': None},
        {'rotulo': 'Meus lotes', 'endpoint': 'lotes', 'fase': None},
        {'rotulo': 'Mercado (comprar)', 'endpoint': 'mercado', 'fase': None},
        {'rotulo': 'Minhas propostas (compra)', 'endpoint': 'minhas_propostas', 'fase': None},
        {'rotulo': 'Minhas transações (venda)', 'endpoint': 'transacoes', 'fase': None},
        {'rotulo': 'Pontos de coleta', 'endpoint': 'pontos', 'fase': None},
    ]),
    (EmpresaCompradora, [
        {'rotulo': 'Meus materiais', 'endpoint': 'materiais', 'fase': None},
        {'rotulo': 'Meus lotes', 'endpoint': 'lotes', 'fase': None},
        {'rotulo': 'Mercado (comprar)', 'endpoint': 'mercado', 'fase': None},
        {'rotulo': 'Minhas propostas (compra)', 'endpoint': 'minhas_propostas', 'fase': None},
        {'rotulo': 'Minhas transações (venda)', 'endpoint': 'transacoes', 'fase': None},
        {'rotulo': 'Pontos de coleta', 'endpoint': 'pontos', 'fase': None},
    ]),
    (IndustriaTransformadora, [
        {'rotulo': 'Mercado (como compradora)', 'endpoint': 'mercado', 'fase': None},
        {'rotulo': 'Minhas propostas (compra)', 'endpoint': 'minhas_propostas', 'fase': None},
        {'rotulo': 'Materiais recebidos', 'endpoint': 'materiais', 'fase': None},
        {'rotulo': 'Pontos de coleta', 'endpoint': 'pontos', 'fase': None},
    ]),
]

def obter_usuario_service():
    return UsuarioService(
        UsuarioDAO(Repositorio())
    )

def usuario_atual():
    usuario_id = session.get('usuario_id')

    return obter_usuario_service().buscar_por_id(
        usuario_id
    )

def login_obrigatorio(view):
    @wraps(view)
    def decorado(*args, **kwargs):
        if usuario_atual() is None:
            flash('Faça login para continuar.', 'info')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return decorado


def menu_do_usuario(usuario):
    for classe, itens in MENU_POR_PERFIL:
        if isinstance(usuario, classe):
            return itens
    return []


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        senha = request.form.get('senha', '')

        try:
            usuario = obter_usuario_service().autenticar(
                email,
                senha,
            )
        except CredenciaisInvalidasError as erro:
            flash(str(erro), 'error')
            return render_template('login.html')

        session['usuario_id'] = str(usuario.id)

        flash(
            f'Bem-vindo(a), {usuario.nome}!',
            'success',
        )
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('home'))


@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html', perfis=PERFIS)


@app.route('/cadastro/<perfil>', methods=['GET', 'POST'])
def cadastro_perfil(perfil):
    info_perfil = PERFIS_POR_CHAVE.get(perfil)

    if info_perfil is None:
        abort(404)

    if request.method == 'POST':
        try:
            obter_usuario_service().cadastrar(
                perfil=perfil,
                nome=request.form.get('nome', ''),
                email=request.form.get('email', ''),
                senha=request.form.get('senha', ''),
                telefone=request.form.get('telefone', ''),
                endereco=request.form.get('endereco', ''),
                documento=request.form.get('documento', ''),
            )
        except ValueError as erro:
            flash(str(erro), 'error')
            return render_template(
                'cadastro_formulario.html',
                perfil=info_perfil,
            )

        flash(
            'Cadastro realizado com sucesso! '
            'Faça login para continuar.',
            'success',
        )
        return redirect(url_for('login'))

    return render_template(
        'cadastro_formulario.html',
        perfil=info_perfil,
    )


@app.route('/dashboard')
@login_obrigatorio
def dashboard():
    usuario = usuario_atual()

    if isinstance(usuario, UsuarioComum):
        return render_template('inicio.html', usuario=usuario)

    return render_template(
        'dashboard.html',
        usuario=usuario,
        perfil_nome=type(usuario).__name__,
        menu=menu_do_usuario(usuario),
    )


@app.route('/perfil', methods=['GET', 'POST'])
@login_obrigatorio
def perfil():
    usuario = usuario_atual()

    if request.method == 'POST':
        try:
            obter_usuario_service().atualizar_perfil(
                usuario=usuario,
                nome=request.form.get('nome', ''),
                email=request.form.get('email', ''),
                telefone=request.form.get('telefone', ''),
                endereco=request.form.get('endereco', ''),
            )
        except ValueError as erro:
            flash(str(erro), 'error')
            return render_template(
                'perfil.html',
                usuario=usuario,
            )

        flash('Perfil atualizado com sucesso.', 'success')
        return redirect(url_for('perfil'))

    return render_template(
        'perfil.html',
        usuario=usuario,
    )
