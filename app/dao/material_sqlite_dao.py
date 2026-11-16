from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
from app.model.enums import StatusMaterial
from app.model.material import Material, EventoRastreio, AvaliacaoQualidade


class MaterialSQLiteDAO:
    """Grava e consulta materiais sem confirmar a transação recebida."""

    def __init__(self, conexao):
        self._conexao = conexao

    def adicionar(self, material):
        if (
            material.status == StatusMaterial.EM_LOTE
            or material.loteAtual is not None
        ):
            raise ValueError(
                "A persistência de materiais em lote ainda não foi implementada."
            )

        existente = self._conexao.execute(
            "SELECT 1 FROM materiais WHERE id = ?",
            (str(material.id),),
        ).fetchone()

        if existente is not None:
            raise ValueError("O material já está cadastrado.")

        self._conexao.execute("SAVEPOINT adicionar_material")

        try:
            self._conexao.execute(
                "INSERT INTO materiais "
                "(id, tipo_material_id, responsavel_atual_id, peso_kg, "
                "condicao_declarada, observacoes_declaradas, status, data_registro) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(material.id),
                    str(material.tipoMaterial.id),
                    str(material.responsavelAtual.id),
                    material.pesoKg,
                    material.condicaoDeclarada.value,
                    material.observacoesDeclaradas,
                    material.status.value,
                    material.dataRegistro.isoformat(),
                ),
            )

            for ordem, evento in enumerate(material.obterHistorico()):
                self._conexao.execute(
                    "INSERT INTO eventos_rastreio "
                    "(id, material_id, ordem, tipo, descricao, data_evento) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        str(evento.id),
                        str(material.id),
                        ordem,
                        evento.tipo.value,
                        evento.descricao,
                        evento.dataEvento.isoformat(),
                    ),
                )

            for ordem, avaliacao in enumerate(material.obterAvaliacoes()):
                self._conexao.execute(
                    "INSERT INTO avaliacoes_qualidade "
                    "(id, material_id, ordem, condicao_detectada, confianca, "
                    "observacoes, data_avaliacao) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(avaliacao.id),
                        str(material.id),
                        ordem,
                        avaliacao.condicaoDetectada.value,
                        avaliacao.confianca,
                        avaliacao.observacoes,
                        avaliacao.dataAvaliacao.isoformat(),
                    ),
                )

        except Exception:
            self._conexao.execute(
                "ROLLBACK TO SAVEPOINT adicionar_material"
            )
            raise
        finally:
            self._conexao.execute(
                "RELEASE SAVEPOINT adicionar_material"
            )

        return material

    def buscar_por_id(self, material_id):
        registro = self._conexao.execute(
            "SELECT * FROM materiais WHERE id = ?",
            (str(material_id),),
        ).fetchone()

        return None if registro is None else self._converter(registro)

    def listar_por_responsavel(self, usuario):
        registros = self._conexao.execute(
            "SELECT * FROM materiais "
            "WHERE responsavel_atual_id = ? ORDER BY rowid",
            (str(usuario.id),),
        ).fetchall()

        return [self._converter(registro) for registro in registros]

    def _converter(self, registro):
        tipo = TipoMaterialSQLiteDAO(self._conexao).buscar_por_id(
            registro["tipo_material_id"]
        )

        usuario = UsuarioSQLiteDAO(self._conexao).buscar_por_id(
            registro["responsavel_atual_id"]
        )

        eventos = self._conexao.execute(
            "SELECT * FROM eventos_rastreio "
            "WHERE material_id = ? ORDER BY ordem",
            (registro["id"],),
        ).fetchall()

        avaliacoes = self._conexao.execute(
            "SELECT * FROM avaliacoes_qualidade "
            "WHERE material_id = ? ORDER BY ordem",
            (registro["id"],),
        ).fetchall()

        return Material.reconstituir(
            identificador=registro["id"],
            tipoMaterial=tipo,
            pesoKg=registro["peso_kg"],
            condicaoDeclarada=registro["condicao_declarada"],
            responsavelAtual=usuario,
            status=registro["status"],
            dataRegistro=registro["data_registro"],
            observacoesDeclaradas=registro["observacoes_declaradas"],
            eventos=[
                EventoRastreio.reconstituir(
                    item["id"],
                    item["tipo"],
                    item["descricao"],
                    item["data_evento"],
                )
                for item in eventos
            ],
            avaliacoes=[
                AvaliacaoQualidade.reconstituir(
                    item["id"],
                    item["condicao_detectada"],
                    item["confianca"],
                    item["data_avaliacao"],
                    item["observacoes"],
                )
                for item in avaliacoes
            ],
        )

    def atualizar(self, material):
        if (
            material.status == StatusMaterial.EM_LOTE
            or material.loteAtual is not None
        ):
            raise ValueError(
                "A persistência de materiais em lote ainda não foi implementada."
            )

        self._conexao.execute("SAVEPOINT atualizar_material")

        try:
            anterior = self.buscar_por_id(material.id)

            if anterior is None:
                raise ValueError("Material não encontrado.")

            if (
                anterior.tipoMaterial.id != material.tipoMaterial.id
                or anterior.pesoKg != material.pesoKg
                or anterior.condicaoDeclarada != material.condicaoDeclarada
                or anterior.observacoesDeclaradas != material.observacoesDeclaradas
                or anterior.dataRegistro != material.dataRegistro
            ):
                raise ValueError(
                    "Os dados originais do cadastro não podem ser alterados."
                )

            eventos = material.obterHistorico()
            avaliacoes = material.obterAvaliacoes()
            eventos_anteriores = anterior.obterHistorico()
            avaliacoes_anteriores = anterior.obterAvaliacoes()

            for antigos, atuais, atributos in (
                (
                    eventos_anteriores,
                    eventos,
                    ("id", "tipo", "descricao", "dataEvento"),
                ),
                (
                    avaliacoes_anteriores,
                    avaliacoes,
                    (
                        "id",
                        "condicaoDetectada",
                        "confianca",
                        "observacoes",
                        "dataAvaliacao",
                    ),
                ),
            ):
                if len(atuais) < len(antigos) or any(
                    any(
                        getattr(a, campo) != getattr(b, campo)
                        for campo in atributos
                    )
                    for a, b in zip(antigos, atuais)
                ):
                    raise ValueError(
                        "O histórico persistido não pode ser removido ou alterado."
                    )

            self._conexao.execute(
                "UPDATE materiais "
                "SET status = ?, responsavel_atual_id = ? "
                "WHERE id = ?",
                (
                    material.status.value,
                    str(material.responsavelAtual.id),
                    str(material.id),
                ),
            )

            for ordem in range(len(eventos_anteriores), len(eventos)):
                evento = eventos[ordem]

                self._conexao.execute(
                    "INSERT INTO eventos_rastreio "
                    "(id, material_id, ordem, tipo, descricao, data_evento) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        str(evento.id),
                        str(material.id),
                        ordem,
                        evento.tipo.value,
                        evento.descricao,
                        evento.dataEvento.isoformat(),
                    ),
                )

            for ordem in range(len(avaliacoes_anteriores), len(avaliacoes)):
                avaliacao = avaliacoes[ordem]

                self._conexao.execute(
                    "INSERT INTO avaliacoes_qualidade "
                    "(id, material_id, ordem, condicao_detectada, confianca, "
                    "observacoes, data_avaliacao) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(avaliacao.id),
                        str(material.id),
                        ordem,
                        avaliacao.condicaoDetectada.value,
                        avaliacao.confianca,
                        avaliacao.observacoes,
                        avaliacao.dataAvaliacao.isoformat(),
                    ),
                )

        except Exception:
            self._conexao.execute(
                "ROLLBACK TO SAVEPOINT atualizar_material"
            )
            raise
        finally:
            self._conexao.execute(
                "RELEASE SAVEPOINT atualizar_material"
            )

        return material