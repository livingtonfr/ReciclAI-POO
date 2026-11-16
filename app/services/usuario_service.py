from werkzeug.security import generate_password_hash

from app.model.usuario import (
    UsuarioComum,
    Catador,
    Cooperativa,
    EmpresaCompradora,
    IndustriaTransformadora,
)

class CredenciaisInvalidasError(ValueError):
    """O e-mail ou a senha informados são inválidos."""


class UsuarioService:
    """Coordena consultas e autenticação de usuários."""

    PERFIS_CADASTRO = {
        "comum": (UsuarioComum, None),
        "catador": (Catador, "cpf"),
        "cooperativa": (Cooperativa, "cnpj"),
        "empresa": (EmpresaCompradora, "cnpj"),
        "industria": (IndustriaTransformadora, "cnpj"),
    }

    def __init__(self, usuario_dao):
        self._usuario_dao = usuario_dao

    def buscar_por_id(self, usuario_id):
        if usuario_id is None:
            return None

        return self._usuario_dao.buscar_por_id(usuario_id)

    def autenticar(self, email, senha):
        usuario = self._usuario_dao.buscar_por_email(email)

        if usuario is None or not usuario.verificarSenha(senha):
            raise CredenciaisInvalidasError(
                "E-mail ou senha inválidos."
            )

        return usuario

    def cadastrar(
        self,
        perfil,
        nome,
        email,
        senha,
        telefone,
        endereco,
        documento="",
    ):
        configuracao = self.PERFIS_CADASTRO.get(perfil)

        if configuracao is None:
            raise ValueError("Perfil de cadastro inválido.")

        classe, campo_documento = configuracao

        nome = nome.strip()
        email = email.strip().lower()
        telefone = telefone.strip()
        endereco = endereco.strip()
        documento = documento.strip()

        obrigatorios = [nome, email, senha, telefone, endereco]

        if campo_documento is not None:
            obrigatorios.append(documento)

        if not all(obrigatorios):
            raise ValueError(
                "Preencha todos os campos obrigatórios."
            )

        if "@" not in email:
            raise ValueError("Informe um e-mail válido.")

        if len(senha) < 6:
            raise ValueError(
                "A senha deve ter pelo menos 6 caracteres."
            )

        if self._usuario_dao.buscar_por_email(email) is not None:
            raise ValueError(
                "Já existe uma conta cadastrada com este e-mail."
            )

        senha_hash = generate_password_hash(senha)

        argumentos = [
            nome,
            email,
            senha_hash,
            telefone,
            endereco,
        ]

        if campo_documento is not None:
            argumentos.append(documento)

        usuario = classe(*argumentos)

        return self._usuario_dao.adicionar(usuario)

    def atualizar_perfil(
        self,
        usuario,
        nome,
        email,
        telefone,
        endereco,
    ):
        if (
            usuario is None
            or self._usuario_dao.buscar_por_id(usuario.id)
            is not usuario
        ):
            raise ValueError("Usuário não encontrado.")

        nome = nome.strip()
        email = email.strip().lower()
        telefone = telefone.strip()
        endereco = endereco.strip()

        if not all([nome, email, telefone, endereco]):
            raise ValueError("Preencha todos os campos.")

        if "@" not in email:
            raise ValueError("Informe um e-mail válido.")

        usuario_com_email = self._usuario_dao.buscar_por_email(
            email
        )

        if (
            usuario_com_email is not None
            and usuario_com_email is not usuario
        ):
            raise ValueError(
                "Este e-mail já está em uso por outra conta."
            )

        usuario.atualizarPerfil(
            nome=nome,
            email=email,
            telefone=telefone,
            endereco=endereco,
        )

        return usuario