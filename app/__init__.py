from flask import Flask

app = Flask(__name__, template_folder='view')
app.secret_key = 'reciclai-dev-secret'

from app.controller import auth
from app.controller import materiais
from app.controller import ia
from app.controller import lotes
from app.controller import transacoes
