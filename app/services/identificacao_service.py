from app.model.usuario import UsuarioComum


class AcessoIdentificacaoNegadoError(PermissionError):
    """O perfil não pode utilizar a identificação de resíduos."""


class IdentificacaoService:
    def __init__(self, servico_visao):
        self._servico_visao = servico_visao

    def identificar(self, usuario, foto):
        if not isinstance(usuario, UsuarioComum):
            raise AcessoIdentificacaoNegadoError(
                "A identificação está disponível ao usuário comum."
            )

        return usuario.identificarResiduo(
            foto,
            self._servico_visao,
        )