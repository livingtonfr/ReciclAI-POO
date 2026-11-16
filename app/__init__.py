from flask import Flask

from app.config import Config


app = Flask(__name__, template_folder="view")
app.config.from_object(Config)


# As rotas são importadas depois da criação da aplicação,
# pois os controllers utilizam a instância "app".
from app.controller import auth
from app.controller import materiais
from app.controller import ia
from app.controller import lotes
from app.controller import transacoes
from app.controller import pontos
from app.controller import admin
from app.controller import erros
from app.controller import api

# Conexão SQLite por requisição, commit/rollback e fechamento.
from app.database import contexto

contexto.registrar(app)
