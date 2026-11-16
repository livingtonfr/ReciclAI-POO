from app.model.usuario import PERFIS_USUARIO, Usuario


class UsuarioSQLiteDAO:
    """Grava e consulta usuários na transação recebida."""

    def __init__(self, conexao):
        self._conexao = conexao

    @staticmethod
    def _converter(registro):
        if registro is None:
            return None

        return Usuario.reconstituir(
            perfil=registro["perfil"],
            identificador=registro["id"],
            nome=registro["nome"],
            email=registro["email"],
            senhaHash=registro["senha_hash"],
            telefone=registro["telefone"],
            endereco=registro["endereco"],
            criadoEm=registro["criado_em"],
            latitude=registro["latitude"],
            longitude=registro["longitude"],
            cpf=registro["cpf"],
            cnpj=registro["cnpj"],
            statusValidacao=registro["status_validacao"],
        )

    def buscar_por_id(self, usuario_id):
        registro = self._conexao.execute(
            "SELECT * FROM usuarios WHERE id = ?",
            (str(usuario_id),),
        ).fetchone()

        return self._converter(registro)

    def buscar_por_email(self, email):
        registro = self._conexao.execute(
            "SELECT * FROM usuarios WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()

        return self._converter(registro)

    def adicionar(self, usuario):
        perfil = next(
            (
                nome
                for nome, (classe, _) in PERFIS_USUARIO.items()
                if type(usuario) is classe
            ),
            None,
        )

        if perfil is None:
            raise ValueError("Perfil de usuário inválido.")

        if self.buscar_por_id(usuario.id) is not None:
            raise ValueError("O usuário já está cadastrado.")

        if self.buscar_por_email(usuario.email) is not None:
            raise ValueError(
                "Já existe uma conta cadastrada com este e-mail."
            )

        status = getattr(usuario, "statusValidacao", None)

        self._conexao.execute(
            "INSERT INTO usuarios "
            "(id, perfil, nome, email, senha_hash, telefone, "
            "endereco, latitude, longitude, criado_em, cpf, "
            "cnpj, status_validacao) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(usuario.id),
                perfil,
                usuario.nome,
                usuario.email.strip().lower(),
                usuario.senhaHash,
                usuario.telefone,
                usuario.endereco,
                usuario.latitude,
                usuario.longitude,
                usuario.criadoEm.isoformat(),
                getattr(usuario, "cpf", None),
                getattr(usuario, "cnpj", None),
                status.value if status is not None else None,
            ),
        )

        return usuario

    def atualizar_perfil(
        self, usuario_id, nome, email, telefone, endereco
    ):
        usuario = self.buscar_por_id(usuario_id)

        if usuario is None:
            raise ValueError("Usuário não encontrado.")

        outro = self.buscar_por_email(email)

        if outro is not None and outro.id != usuario.id:
            raise ValueError(
                "Este e-mail já está em uso por outra conta."
            )

        usuario.atualizarPerfil(
            nome=nome,
            email=email,
            telefone=telefone,
            endereco=endereco,
        )

        cursor = self._conexao.execute(
            "UPDATE usuarios SET nome = ?, email = ?, telefone = ?, "
            "endereco = ?, latitude = ?, longitude = ? WHERE id = ?",
            (
                usuario.nome,
                usuario.email,
                usuario.telefone,
                usuario.endereco,
                usuario.latitude,
                usuario.longitude,
                str(usuario.id),
            ),
        )

        if cursor.rowcount != 1:
            raise ValueError("Usuário não encontrado.")

        return usuario