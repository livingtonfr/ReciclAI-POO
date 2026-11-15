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
from werkzeug.security import generate_password_hash

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

# Menu do /dashboard por perfil (isinstance = polimorfismo na escolha do menu).
# UsuarioComum não usa esse menu: tem a tela "Início" própria (ações rápidas).
# Itens sem "endpoint" ainda não têm rota (entram nas próximas fases) e
# aparecem só com o rótulo e a fase em que a função é ativada.
MENU_POR_PERFIL = [
    (Catador, [
        {'rotulo': 'Meus materiais', 'endpoint': 'materiais', 'fase': None},
        {'rotulo': 'Meus lotes', 'endpoint': 'lotes', 'fase': None},
        {'rotulo': 'Mercado e transações', 'endpoint': None, 'fase': 'Fase 7'},
    ]),
    (Cooperativa, [
        {'rotulo': 'Meus materiais', 'endpoint': 'materiais', 'fase': None},
        {'rotulo': 'Meus lotes', 'endpoint': 'lotes', 'fase': None},
        {'rotulo': 'Mercado e transações', 'endpoint': None, 'fase': 'Fase 7'},
    ]),
    (EmpresaCompradora, [
        {'rotulo': 'Meus materiais', 'endpoint': 'materiais', 'fase': None},
        {'rotulo': 'Meus lotes', 'endpoint': 'lotes', 'fase': None},
        {'rotulo': 'Mercado e transações', 'endpoint': None, 'fase': 'Fase 7'},
    ]),
    (IndustriaTransformadora, [
        {'rotulo': 'Mercado (como compradora)', 'endpoint': None, 'fase': 'Fase 7'},
    ]),
]


def usuario_atual():
    usuario_id = session.get('usuario_id')
    if usuario_id is None:
        return None
    return Repositorio().buscarUsuarioPorId(usuario_id)


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
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        usuario = Repositorio().buscarUsuarioPorEmail(email)

        if usuario is None or not usuario.verificarSenha(senha):
            flash('E-mail ou senha inválidos.', 'error')
            return render_template('login.html')

        session['usuario_id'] = str(usuario.id)
        flash(f'Bem-vindo(a), {usuario.nome}!', 'success')
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
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        telefone = request.form.get('telefone', '').strip()
        endereco = request.form.get('endereco', '').strip()
        documento = request.form.get('documento', '').strip()

        campos_obrigatorios = [nome, email, senha, telefone, endereco]
        if info_perfil['documento'] is not None:
            campos_obrigatorios.append(documento)

        if not all(campos_obrigatorios):
            flash('Preencha todos os campos obrigatórios.', 'error')
            return render_template('cadastro_formulario.html', perfil=info_perfil)

        if '@' not in email:
            flash('Informe um e-mail válido.', 'error')
            return render_template('cadastro_formulario.html', perfil=info_perfil)

        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('cadastro_formulario.html', perfil=info_perfil)

        if Repositorio().buscarUsuarioPorEmail(email) is not None:
            flash('Já existe uma conta cadastrada com este e-mail.', 'error')
            return render_template('cadastro_formulario.html', perfil=info_perfil)

        senha_hash = generate_password_hash(senha)
        classe = info_perfil['classe']

        if info_perfil['documento'] is not None:
            usuario = classe(nome, email, senha_hash, telefone, endereco, documento)
        else:
            usuario = classe(nome, email, senha_hash, telefone, endereco)

        Repositorio().usuarios.append(usuario)

        flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro_formulario.html', perfil=info_perfil)


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
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        telefone = request.form.get('telefone', '').strip()
        endereco = request.form.get('endereco', '').strip()

        if not all([nome, email, telefone, endereco]):
            flash('Preencha todos os campos.', 'error')
            return render_template('perfil.html', usuario=usuario)

        if '@' not in email:
            flash('Informe um e-mail válido.', 'error')
            return render_template('perfil.html', usuario=usuario)

        usuario_com_email = Repositorio().buscarUsuarioPorEmail(email)
        if usuario_com_email is not None and usuario_com_email is not usuario:
            flash('Este e-mail já está em uso por outra conta.', 'error')
            return render_template('perfil.html', usuario=usuario)

        usuario.atualizarPerfil(nome=nome, email=email, telefone=telefone, endereco=endereco)
        flash('Perfil atualizado com sucesso.', 'success')
        return redirect(url_for('perfil'))

    return render_template('perfil.html', usuario=usuario)
