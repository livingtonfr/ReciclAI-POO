class CredenciaisInvalidasError(ValueError):
    """O e-mail ou a senha informados são inválidos."""


class UsuarioService:
    """Coordena consultas e autenticação de usuários."""

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