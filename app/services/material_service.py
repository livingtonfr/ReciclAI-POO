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

    def __init__(self, material_dao, tipo_material_dao=None, servico_visao=None, servico_precificacao=None):
        self._material_dao = material_dao
        self._tipo_material_dao = tipo_material_dao
        self._servico_visao = servico_visao
        self._servico_precificacao = servico_precificacao

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

        if material.responsavelAtual.id != usuario.id:
            raise AcessoMaterialNegadoError(
                "O material pertence a outro responsável."
            )
        return material

    def registrar(self, usuario, tipo, peso_kg, condicao, observacoes=None):
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
        return self._material_dao.atualizar(material)

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

    def _validar_operador(self, usuario):
        if not isinstance(
            usuario,
            (Catador, Cooperativa, EmpresaCompradora),
        ):
            raise AcessoMaterialNegadoError(
                "Este perfil não pode operar materiais."
            )

    def avaliar(self, material_id, usuario, foto):
        self._validar_operador(usuario)
        material = self.buscar_do_usuario(material_id, usuario)

        if self._servico_visao is None:
            raise RuntimeError(
                "O serviço de visão não foi configurado."
            )

        avaliacao = self._servico_visao.avaliarMaterial(
            material,
            foto,
        )

        self._material_dao.atualizar(material)
        return avaliacao

    def cotar(self, material_id, usuario, horizonte_dias):
        self._validar_operador(usuario)
        material = self.buscar_do_usuario(material_id, usuario)

        if self._servico_precificacao is None:
            raise RuntimeError(
                "O serviço de precificação não foi configurado."
            )

        return usuario.solicitarPrecificacaoMaterial(
            material,
            horizonte_dias,
            self._servico_precificacao,
        )