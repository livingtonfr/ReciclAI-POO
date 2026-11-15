from flask import render_template, request, redirect, url_for, flash, abort

from app import app

# Perfis exibidos na seleção de cadastro (um para cada subclasse concreta de Usuario).
# "chave" é usada na URL e no nome da classe CSS que define a cor do card.
PERFIS = [
    {'chave': 'comum', 'nome': 'Usuário Comum', 'icone': '👤',
     'descricao': 'Descarte correto e informação', 'selo': 'Gratuito'},
    {'chave': 'catador', 'nome': 'Catador', 'icone': '♻️',
     'descricao': 'Vender material com melhor preço', 'selo': 'Gratuito'},
    {'chave': 'cooperativa', 'nome': 'Cooperativa', 'icone': '🏢',
     'descricao': 'Gestão, precificação e certificação', 'selo': 'Premium'},
    {'chave': 'empresa', 'nome': 'Empresa Compradora', 'icone': '🏭',
     'descricao': 'Fornecimento confiável e rastreável', 'selo': 'Premium'},
    {'chave': 'industria', 'nome': 'Indústria', 'icone': '⚙️',
     'descricao': 'Insumo reciclado com rastreabilidade', 'selo': 'Premium'},
]


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # A autenticação real entra na Fase 4.
        flash('A autenticação será ativada na Fase 4.', 'info')
    return render_template('login.html')


@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html', perfis=PERFIS)


@app.route('/cadastro/<perfil>')
def cadastro_perfil(perfil):
    if perfil not in [p['chave'] for p in PERFIS]:
        abort(404)
    # O formulário de cada perfil entra na Fase 4.
    flash('O formulário de cadastro será ativado na Fase 4.', 'info')
    return redirect(url_for('cadastro'))
