from werkzeug.security import generate_password_hash

from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.model.enums import CategoriaMaterial
from app.model.material import TipoMaterial
from app.model.usuario import PERFIS_USUARIO

SENHA_DEMO = "123456"

# (perfil, nome, e-mail, telefone, endereço, documento)
USUARIOS_DEMO = (
    ("comum", "Ana", "ana@email.com", "62999999999",
     "Rua A, Goiânia", None),
    ("catador", "Carlos", "carlos@email.com", "62988888888",
     "Rua B, Goiânia", "12345678900"),
    ("cooperativa", "Cooperativa Verde", "cooperativa@email.com",
     "62977777777", "Rua C, Goiânia", "12345678000199"),
    ("empresa", "Empresa Recicladora", "empresa@email.com",
     "62966666666", "Rua D, Goiânia", "98765432000188"),
    ("industria", "Indústria Circular", "industria@email.com",
     "62955555555", "Rua E, Goiânia", "11223344000155"),
)

TIPOS_DEMO = (
    ("PET", "Plástico PET reciclável", CategoriaMaterial.PLASTICO),
    ("Vidro", "Embalagem de vidro reciclável", CategoriaMaterial.VIDRO),
    ("Papel", "Papel e papelão recicláveis", CategoriaMaterial.PAPEL),
    ("Metal", "Latas e sucata metálica", CategoriaMaterial.METAL),
)

# Ordem compatível com as chaves estrangeiras (filhas antes das mães).
TABELAS_EM_ORDEM_DE_LIMPEZA = (
    "certificados",
    "transacoes",
    "vinculos_lotes_atuais",
    "lotes_materiais",
    "lotes",
    "avaliacoes_qualidade",
    "eventos_rastreio",
    "materiais",
    "usuarios",
    "tipos_material",
)


def semear_demo(conexao):
    """Cria usuários e tipos de demonstração que ainda não existem.

    É repetível: nunca duplica registros, nunca altera contas existentes
    (inclusive a senha) e nunca apaga dados.
    """
    usuarios = UsuarioSQLiteDAO(conexao)

    for perfil, nome, email, telefone, endereco, documento in USUARIOS_DEMO:
        if usuarios.buscar_por_email(email) is not None:
            continue

        classe, campo_documento = PERFIS_USUARIO[perfil]

        argumentos = [
            nome,
            email,
            generate_password_hash(SENHA_DEMO),
            telefone,
            endereco,
        ]

        if campo_documento is not None:
            argumentos.append(documento)

        usuarios.adicionar(classe(*argumentos))

    tipos = TipoMaterialSQLiteDAO(conexao)
    existentes = {tipo.nome for tipo in tipos.listar()}

    for nome, descricao, categoria in TIPOS_DEMO:
        if nome not in existentes:
            tipos.adicionar(TipoMaterial(nome, descricao, categoria))


def limpar_dados(conexao):
    """Apaga TODOS os registros, preservando a estrutura das tabelas."""
    for tabela in TABELAS_EM_ORDEM_DE_LIMPEZA:
        conexao.execute(f"DELETE FROM {tabela}")


def resetar_banco(conexao):
    """Apaga tudo e recarrega a demonstração (na transação recebida)."""
    limpar_dados(conexao)
    semear_demo(conexao)
