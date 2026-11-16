class UsuarioDAO:
    """Consulta usuários no repositório em memória."""

    def __init__(self, repositorio):
        self._repositorio = repositorio

    def buscar_por_id(self, usuario_id):
        for usuario in self._repositorio.usuarios:
            if str(usuario.id) == str(usuario_id):
                return usuario

        return None

    def buscar_por_email(self, email):
        email_normalizado = email.strip().lower()

        for usuario in self._repositorio.usuarios:
            if usuario.email.strip().lower() == email_normalizado:
                return usuario

        return None

    def adicionar(self, usuario):
        if self.buscar_por_id(usuario.id) is not None:
            raise ValueError("O usuário já está cadastrado.")

        if self.buscar_por_email(usuario.email) is not None:
            raise ValueError(
                "Já existe uma conta cadastrada com este e-mail."
            )

        self._repositorio.usuarios.append(usuario)
        return usuario