from app.dao.material_sqlite_dao import MaterialSQLiteDAO
from app.model.enums import StatusLote, StatusMaterial
from app.model.lote import LoteMaterial
from app.model.material import Material
from app.model.usuario import (
    Catador,
    Cooperativa,
    EmpresaCompradora,
)
from app.model.validacoes import validar_peso_lote


class LoteSQLiteDAO:
    """Persiste lotes na transação recebida, sem executar commit."""

    def __init__(self, conexao):
        self._conexao = conexao

    def adicionar(self, lote):
        if not isinstance(lote, LoteMaterial):
            raise TypeError("Lote inválido.")

        if lote.status not in (
            StatusLote.EM_FORMACAO,
            StatusLote.DISPONIVEL,
        ):
            raise ValueError("A inclusão exige um lote ativo.")

        if lote.transacoes:
            raise ValueError(
                "A persistência das transações ainda não foi implementada."
            )

        if not isinstance(
            lote.criador,
            (Catador, Cooperativa, EmpresaCompradora),
        ):
            raise ValueError("Perfil de criador inválido.")

        materiais = lote.materiais

        if not materiais or len({m.id for m in materiais}) != len(materiais):
            raise ValueError(
                "Composição vazia ou com material repetido."
            )

        validar_peso_lote(lote.calcularPesoTotal())

        if lote.pesoRegistrado is not None:
            validar_peso_lote(lote.pesoRegistrado)

        tipo = materiais[0].tipoMaterial

        for material in materiais:
            if (
                material.loteAtual is not lote
                or material.status != StatusMaterial.EM_LOTE
                or material.responsavelAtual is not lote.criador
                or material.tipoMaterial is not tipo
            ):
                raise ValueError(
                    "Os vínculos do lote estão inconsistentes."
                )

        self._conexao.execute("SAVEPOINT adicionar_lote")

        try:
            existente = self._conexao.execute(
                "SELECT 1 FROM lotes WHERE id = ?",
                (str(lote.id),),
            ).fetchone()

            if existente is not None:
                raise ValueError("O lote já está cadastrado.")

            dao_material = MaterialSQLiteDAO(self._conexao)

            for material in materiais:
                registro = self._conexao.execute(
                    "SELECT status, responsavel_atual_id "
                    "FROM materiais WHERE id = ?",
                    (str(material.id),),
                ).fetchone()

                if registro is None or registro["status"] != "DISPONIVEL":
                    raise ValueError(
                        "O material deve estar persistido como DISPONIVEL."
                    )

                if registro["responsavel_atual_id"] != str(lote.criador.id):
                    raise ValueError(
                        "O responsável persistido difere do criador."
                    )

                vinculo = self._conexao.execute(
                    "SELECT 1 FROM vinculos_lotes_atuais "
                    "WHERE material_id = ?",
                    (str(material.id),),
                ).fetchone()

                if vinculo is not None:
                    raise ValueError(
                        "O material já possui vínculo persistido."
                    )

            self._conexao.execute(
                "INSERT INTO lotes "
                "(id, criador_id, data_criacao, status, peso_registrado) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    str(lote.id),
                    str(lote.criador.id),
                    lote.dataCriacao.isoformat(),
                    lote.status.value,
                    lote.pesoRegistrado,
                ),
            )

            for ordem, material in enumerate(materiais):
                # Reaproveita a validação do histórico sem alterar
                # o objeto original nem seu vínculo com o lote.
                copia = Material.reconstituir(
                    identificador=material.id,
                    tipoMaterial=material.tipoMaterial,
                    pesoKg=material.pesoKg,
                    condicaoDeclarada=material.condicaoDeclarada,
                    responsavelAtual=material.responsavelAtual,
                    status="DISPONIVEL",
                    dataRegistro=material.dataRegistro.isoformat(),
                    eventos=material.obterHistorico(),
                    avaliacoes=material.obterAvaliacoes(),
                    observacoesDeclaradas=material.observacoesDeclaradas,
                )

                dao_material.atualizar(copia)

                self._conexao.execute(
                    "INSERT INTO lotes_materiais "
                    "(lote_id, material_id, ordem) VALUES (?, ?, ?)",
                    (
                        str(lote.id),
                        str(material.id),
                        ordem,
                    ),
                )

                self._conexao.execute(
                    "INSERT INTO vinculos_lotes_atuais "
                    "(material_id, lote_id) VALUES (?, ?)",
                    (str(material.id), str(lote.id)),
                )

                self._conexao.execute(
                    "UPDATE materiais SET status = 'EM_LOTE' "
                    "WHERE id = ?",
                    (str(material.id),),
                )

        except Exception:
            self._conexao.execute(
                "ROLLBACK TO SAVEPOINT adicionar_lote"
            )
            raise
        finally:
            self._conexao.execute(
                "RELEASE SAVEPOINT adicionar_lote"
            )

        return lote