from app.model.usuario import (
    Catador,
    Cooperativa,
    EmpresaCompradora,
    IndustriaTransformadora,
)


class MaterialNaoEncontradoError(LookupError):
    """O material solicitado não existe."""


class AcessoMaterialNegadoError(PermissionError):
    """O usuário não pode consultar esse material."""


class MaterialService:
    """Coordena as consultas e permissões de materiais."""

    PERFIS_TITULARES = (
        Catador,
        Cooperativa,
        EmpresaCompradora,
        IndustriaTransformadora,
    )

    def __init__(self, material_dao):
        self._material_dao = material_dao

    def _validar_perfil(self, usuario):
        if not isinstance(usuario, self.PERFIS_TITULARES):
            raise AcessoMaterialNegadoError(
                "Este perfil não pode consultar materiais."
            )

    def listar_do_usuario(self, usuario):
        self._validar_perfil(usuario)
        return self._material_dao.listar_por_responsavel(usuario)

    def buscar_do_usuario(self, material_id, usuario):
        self._validar_perfil(usuario)

        material = self._material_dao.buscar_por_id(material_id)

        if material is None:
            raise MaterialNaoEncontradoError(
                "Material não encontrado."
            )

        if material.responsavelAtual is not usuario:
            raise AcessoMaterialNegadoError(
                "O material pertence a outro responsável."
            )

        return material