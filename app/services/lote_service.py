from app.model.enums import StatusMaterial
from app.model.usuario import (
    Catador,
    Cooperativa,
    EmpresaCompradora,
)


class LoteNaoEncontradoError(LookupError):
    """O lote solicitado não existe."""


class AcessoLoteNegadoError(PermissionError):
    """O usuário não pode acessar essa operação de lotes."""


class LoteService:
    """Coordena as consultas dos lotes do criador."""

    PERFIS_OPERADORES = (
        Catador,
        Cooperativa,
        EmpresaCompradora,
    )

    def __init__(self, lote_dao, material_dao, servico_precificacao=None):
        self._lote_dao = lote_dao
        self._material_dao = material_dao
        self._servico_precificacao = servico_precificacao

    def _validar_perfil(self, usuario):
        if not isinstance(usuario, self.PERFIS_OPERADORES):
            raise AcessoLoteNegadoError(
                "Este perfil não pode gerenciar lotes."
            )

    def listar_do_usuario(self, usuario):
        self._validar_perfil(usuario)
        return self._lote_dao.listar_por_criador(usuario)

    def buscar_do_usuario(self, lote_id, usuario):
        self._validar_perfil(usuario)

        lote = self._lote_dao.buscar_por_id(lote_id)

        if lote is None:
            raise LoteNaoEncontradoError(
                "Lote não encontrado."
            )

        if lote.criador.id != usuario.id:
            raise AcessoLoteNegadoError(
                "O lote pertence a outro criador."
            )

        return lote

    def listar_materiais_disponiveis(self, usuario, excluir=None):
        self._validar_perfil(usuario)

        materiais = self._material_dao.listar_disponiveis_por_responsavel(
            usuario
        )

        return [
            material
            for material in materiais
            if material.status == StatusMaterial.DISPONIVEL
            and (excluir is None or material.id != excluir.id)
        ]

    def _buscar_material_disponivel(self, material_id, usuario):
        materiais = self.listar_materiais_disponiveis(usuario)

        for material in materiais:
            if str(material.id) == str(material_id):
                return material

        raise ValueError(
            "Selecione um material disponível sob "
            "sua responsabilidade."
        )

    def criar(self, usuario, material_id):
        self._validar_perfil(usuario)

        material = self._buscar_material_disponivel(
            material_id,
            usuario,
        )

        lote = material.responsavelAtual.criarLote(material)
        return self._lote_dao.adicionar(lote)

    def adicionar_material(self, lote_id, material_id, usuario):
        lote = self.buscar_do_usuario(lote_id, usuario)

        material = self._buscar_material_disponivel(
            material_id,
            usuario,
        )

        return self._lote_dao.adicionar_material(lote.id, material.id)

    def remover_material(self, lote_id, material_id, usuario):
        lote = self.buscar_do_usuario(lote_id, usuario)

        material = next(
            (
                item
                for item in lote.materiais
                if str(item.id) == str(material_id)
            ),
            None,
        )

        if material is None:
            raise ValueError(
                "Material não encontrado neste lote."
            )

        return self._lote_dao.remover_material(lote.id, material.id)

    def registrar_pesagem(self, lote_id, usuario, peso):
        lote = self.buscar_do_usuario(lote_id, usuario)

        return self._lote_dao.registrar_pesagem(
            lote.id,
            peso,
        )

    def disponibilizar(self, lote_id, usuario):
        lote = self.buscar_do_usuario(lote_id, usuario)

        return self._lote_dao.disponibilizar(lote.id)

    def cancelar(self, lote_id, usuario):
        lote = self.buscar_do_usuario(lote_id, usuario)

        return self._lote_dao.cancelar(lote.id)

    def cotar(self, lote_id, usuario, horizonte_dias):
        lote = self.buscar_do_usuario(lote_id, usuario)

        if self._servico_precificacao is None:
            raise RuntimeError(
                "O serviço de precificação não foi configurado."
            )

        return lote.criador.solicitarPrecificacaoLote(
            lote,
            horizonte_dias,
            self._servico_precificacao,
        )