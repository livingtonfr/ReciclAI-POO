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

    def __init__(self, material_dao, tipo_material_dao=None):
        self._material_dao = material_dao
        self._tipo_material_dao = tipo_material_dao

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

    def registrar(
        self,
        usuario,
        tipo,
        peso_kg,
        condicao,
        observacoes=None,
    ):
        if not isinstance(usuario, Catador):
            raise AcessoMaterialNegadoError(
                "Este perfil não pode cadastrar materiais."
            )

        material = usuario.registrarMaterial(
            tipo,
            peso_kg,
            condicao,
            observacoes,
        )

        return self._material_dao.adicionar(material)

    def disponibilizar(self, material_id, usuario):
        if not isinstance(
            usuario,
            (Catador, Cooperativa, EmpresaCompradora),
        ):
            raise AcessoMaterialNegadoError(
                "Este perfil não pode disponibilizar materiais."
            )

        material = self.buscar_do_usuario(
            material_id,
            usuario,
        )
        material.disponibilizar()
        return material

    def _obter_tipo_material_dao(self):
        if self._tipo_material_dao is None:
            raise RuntimeError(
                "O DAO de tipos de material não foi configurado."
            )

        return self._tipo_material_dao

    def listar_tipos(self):
        return self._obter_tipo_material_dao().listar()

    def buscar_tipo(self, tipo_id):
        return self._obter_tipo_material_dao().buscar_por_id(tipo_id)