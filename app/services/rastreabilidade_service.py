from app.services.material_service import (
    MaterialNaoEncontradoError,
    AcessoMaterialNegadoError,
)


class RastreabilidadeService:
    def __init__(self, material_dao, transacao_dao):
        self._material_dao = material_dao
        self._transacao_dao = transacao_dao

    def consultar_historico(self, material_id, usuario):
        if usuario is None:
            raise AcessoMaterialNegadoError(
                "É necessário estar autenticado."
            )

        material = self._material_dao.buscar_por_id(material_id)

        if material is None:
            raise MaterialNaoEncontradoError(
                "Material não encontrado."
            )

        if material.responsavelAtual is usuario:
            return material.obterHistorico()

        transacoes = (
            self._transacao_dao
            .listar_concluidas_por_material(material)
        )

        participou = any(
            usuario is transacao.vendedor
            or usuario is transacao.comprador
            for transacao in transacoes
        )

        if not participou:
            raise AcessoMaterialNegadoError(
                "Você não pode consultar este histórico."
            )

        return material.obterHistorico()