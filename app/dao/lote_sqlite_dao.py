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

    def buscar_por_id(self, lote_id):
        from app.dao.tipo_material_sqlite_dao import TipoMaterialSQLiteDAO
        from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO
        from app.model.material import EventoRastreio, AvaliacaoQualidade

        registro = self._conexao.execute(
            "SELECT * FROM lotes WHERE id = ?",
            (str(lote_id),),
        ).fetchone()

        if registro is None:
            return None

        if registro["status"] in ("NEGOCIADO", "CANCELADO"):
            return self._reconstituir_encerrado(registro)

        criador = UsuarioSQLiteDAO(self._conexao).buscar_por_id(
            registro["criador_id"]
        )

        composicao = self._conexao.execute(
            "SELECT m.* FROM lotes_materiais AS lm "
            "JOIN materiais AS m ON m.id = lm.material_id "
            "WHERE lm.lote_id = ? ORDER BY lm.ordem",
            (registro["id"],),
        ).fetchall()

        vinculos = self._conexao.execute(
            "SELECT material_id FROM vinculos_lotes_atuais "
            "WHERE lote_id = ?",
            (registro["id"],),
        ).fetchall()

        if (
            {r["id"] for r in composicao}
            != {r["material_id"] for r in vinculos}
        ):
            raise ValueError(
                "A composição e os vínculos atuais estão inconsistentes."
            )

        tipos = {}
        dados_materiais = []

        for item in composicao:
            if item["responsavel_atual_id"] != registro["criador_id"]:
                raise ValueError(
                    "O responsável do material difere do criador."
                )

            tipo_id = item["tipo_material_id"]

            if tipo_id not in tipos:
                tipos[tipo_id] = TipoMaterialSQLiteDAO(
                    self._conexao
                ).buscar_por_id(tipo_id)

            eventos = self._conexao.execute(
                "SELECT * FROM eventos_rastreio "
                "WHERE material_id = ? ORDER BY ordem",
                (item["id"],),
            ).fetchall()

            avaliacoes = self._conexao.execute(
                "SELECT * FROM avaliacoes_qualidade "
                "WHERE material_id = ? ORDER BY ordem",
                (item["id"],),
            ).fetchall()

            dados_materiais.append(
                dict(
                    identificador=item["id"],
                    tipoMaterial=tipos[tipo_id],
                    pesoKg=item["peso_kg"],
                    condicaoDeclarada=item["condicao_declarada"],
                    responsavelAtual=criador,
                    status=item["status"],
                    dataRegistro=item["data_registro"],
                    observacoesDeclaradas=item["observacoes_declaradas"],
                    eventos=[
                        EventoRastreio.reconstituir(
                            e["id"],
                            e["tipo"],
                            e["descricao"],
                            e["data_evento"],
                        )
                        for e in eventos
                    ],
                    avaliacoes=[
                        AvaliacaoQualidade.reconstituir(
                            a["id"],
                            a["condicao_detectada"],
                            a["confianca"],
                            a["data_avaliacao"],
                            a["observacoes"],
                        )
                        for a in avaliacoes
                    ],
                )
            )

        return LoteMaterial.reconstituir_ativo(
            identificador=registro["id"],
            criador=criador,
            dataCriacao=registro["data_criacao"],
            status=registro["status"],
            dadosMateriais=dados_materiais,
            pesoRegistrado=registro["peso_registrado"],
        )

    def atualizar_pesagem_e_estado(self, lote):
        """Atualiza somente pesagem e estado ativo; não salva a composição."""
        if not isinstance(lote, LoteMaterial):
            raise TypeError("Lote inválido.")

        if lote.status not in (
            StatusLote.EM_FORMACAO,
            StatusLote.DISPONIVEL,
        ):
            raise ValueError(
                "Esta operação aceita somente lotes ativos."
            )

        if lote.transacoes:
            raise ValueError(
                "A persistência das transações ainda não foi implementada."
            )

        if lote.pesoRegistrado is not None:
            validar_peso_lote(lote.pesoRegistrado)

        anterior = self.buscar_por_id(lote.id)

        if anterior is None:
            raise ValueError("Lote não encontrado.")

        if (
            anterior.criador.id != lote.criador.id
            or anterior.dataCriacao != lote.dataCriacao
        ):
            raise ValueError(
                "Os dados originais do lote não podem ser alterados."
            )

        if (
            [m.id for m in anterior.materiais]
            != [m.id for m in lote.materiais]
        ):
            raise ValueError(
                "Salve a composição pela operação específica de composição."
            )

        for material in lote.materiais:
            if (
                material.loteAtual is not lote
                or material.status != StatusMaterial.EM_LOTE
                or material.responsavelAtual is not lote.criador
            ):
                raise ValueError(
                    "Os vínculos do lote estão inconsistentes."
                )

        if (
            anterior.status == StatusLote.DISPONIVEL
            and lote.status != StatusLote.DISPONIVEL
        ):
            raise ValueError(
                "Um lote disponibilizado não pode voltar a EM_FORMACAO."
            )

        self._conexao.execute(
            "UPDATE lotes SET peso_registrado = ?, status = ? "
            "WHERE id = ?",
            (
                lote.pesoRegistrado,
                lote.status.value,
                str(lote.id),
            ),
        )

        return lote

    def adicionar_material(self, lote_id, material_id):
        return self._alterar_composicao(
            lote_id,
            material_id,
            incluir=True,
        )

    def remover_material(self, lote_id, material_id):
        return self._alterar_composicao(
            lote_id,
            material_id,
            incluir=False,
        )

    def _alterar_composicao(self, lote_id, material_id, incluir):
        self._conexao.execute("SAVEPOINT alterar_composicao")

        try:
            lote = self.buscar_por_id(lote_id)

            if lote is None:
                raise ValueError("Lote não encontrado.")

            if lote.status != StatusLote.EM_FORMACAO:
                raise ValueError(
                    "A composição só pode mudar em lote EM_FORMACAO."
                )

            if incluir:
                original = MaterialSQLiteDAO(
                    self._conexao
                ).buscar_por_id(material_id)

                if original is None:
                    raise ValueError("Material não encontrado.")

                if original.status != StatusMaterial.DISPONIVEL:
                    raise ValueError(
                        "O material deve estar DISPONIVEL."
                    )

                if original.responsavelAtual.id != lote.criador.id:
                    raise ValueError(
                        "O material pertence a outro responsável."
                    )

                tipo = lote.materiais[0].tipoMaterial

                if original.tipoMaterial.id != tipo.id:
                    raise ValueError(
                        "O material deve possuir o mesmo tipo do lote."
                    )

                vinculo = self._conexao.execute(
                    "SELECT 1 FROM vinculos_lotes_atuais "
                    "WHERE material_id = ?",
                    (str(original.id),),
                ).fetchone()

                if vinculo is not None:
                    raise ValueError(
                        "O material já possui vínculo atual."
                    )

                material = Material.reconstituir(
                    identificador=original.id,
                    tipoMaterial=tipo,
                    pesoKg=original.pesoKg,
                    condicaoDeclarada=original.condicaoDeclarada,
                    responsavelAtual=lote.criador,
                    status=original.status,
                    dataRegistro=original.dataRegistro.isoformat(),
                    eventos=original.obterHistorico(),
                    avaliacoes=original.obterAvaliacoes(),
                    observacoesDeclaradas=original.observacoesDeclaradas,
                )

                lote.adicionarMaterial(material)

                ordem = self._conexao.execute(
                    "SELECT COALESCE(MAX(ordem), -1) + 1 "
                    "FROM lotes_materiais WHERE lote_id = ?",
                    (str(lote.id),),
                ).fetchone()[0]

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

                evento = material.obterHistorico()[-1]

                ordem_evento = self._conexao.execute(
                    "SELECT COALESCE(MAX(ordem), -1) + 1 "
                    "FROM eventos_rastreio WHERE material_id = ?",
                    (str(material.id),),
                ).fetchone()[0]

                self._conexao.execute(
                    "INSERT INTO eventos_rastreio "
                    "(id, material_id, ordem, tipo, descricao, data_evento) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        str(evento.id),
                        str(material.id),
                        ordem_evento,
                        evento.tipo.value,
                        evento.descricao,
                        evento.dataEvento.isoformat(),
                    ),
                )

                estado = "EM_LOTE"

            else:
                material = next(
                    (
                        m
                        for m in lote.materiais
                        if str(m.id) == str(material_id)
                    ),
                    None,
                )

                if material is None:
                    raise ValueError(
                        "O material não pertence a este lote."
                    )

                lote.removerMaterial(material)

                self._conexao.execute(
                    "DELETE FROM vinculos_lotes_atuais "
                    "WHERE material_id = ? AND lote_id = ?",
                    (str(material.id), str(lote.id)),
                )

                self._conexao.execute(
                    "DELETE FROM lotes_materiais "
                    "WHERE lote_id = ? AND material_id = ?",
                    (str(lote.id), str(material.id)),
                )

                estado = "DISPONIVEL"

            self._conexao.execute(
                "UPDATE materiais SET status = ? WHERE id = ?",
                (estado, str(material.id)),
            )

            self._conexao.execute(
                "UPDATE lotes SET peso_registrado = NULL "
                "WHERE id = ?",
                (str(lote.id),),
            )

        except Exception:
            self._conexao.execute(
                "ROLLBACK TO SAVEPOINT alterar_composicao"
            )
            raise
        finally:
            self._conexao.execute(
                "RELEASE SAVEPOINT alterar_composicao"
            )

        return lote

    def cancelar(self, lote_id):
        """Cancela um lote ativo e libera seus materiais atomicamente."""
        self._conexao.execute("SAVEPOINT cancelar_lote")

        try:
            lote = self.buscar_por_id(lote_id)

            if lote is None:
                raise ValueError("Lote não encontrado.")

            lote.cancelar()

            for material in lote.materiais:
                self._conexao.execute(
                    "DELETE FROM vinculos_lotes_atuais "
                    "WHERE material_id = ? AND lote_id = ?",
                    (str(material.id), str(lote.id)),
                )

                self._conexao.execute(
                    "UPDATE materiais SET status = 'DISPONIVEL' "
                    "WHERE id = ?",
                    (str(material.id),),
                )

            self._conexao.execute(
                "UPDATE lotes SET status = 'CANCELADO' "
                "WHERE id = ?",
                (str(lote.id),),
            )

        except Exception:
            self._conexao.execute(
                "ROLLBACK TO SAVEPOINT cancelar_lote"
            )
            raise
        finally:
            self._conexao.execute(
                "RELEASE SAVEPOINT cancelar_lote"
            )

        return lote

    def _reconstituir_encerrado(self, registro):
        from app.dao.usuario_sqlite_dao import UsuarioSQLiteDAO

        vinculo_proprio = self._conexao.execute(
            "SELECT 1 FROM vinculos_lotes_atuais "
            "WHERE lote_id = ?",
            (registro["id"],),
        ).fetchone()

        if vinculo_proprio is not None:
            raise ValueError(
                "Lote encerrado não pode manter vínculos atuais."
            )

        criador = UsuarioSQLiteDAO(self._conexao).buscar_por_id(
            registro["criador_id"]
        )

        composicao = self._conexao.execute(
            "SELECT material_id FROM lotes_materiais "
            "WHERE lote_id = ? ORDER BY ordem",
            (registro["id"],),
        ).fetchall()

        ativos = {}
        materiais = []

        for item in composicao:
            material_id = item["material_id"]

            vinculo = self._conexao.execute(
                "SELECT lote_id FROM vinculos_lotes_atuais "
                "WHERE material_id = ?",
                (material_id,),
            ).fetchone()

            if vinculo is None:
                material = MaterialSQLiteDAO(
                    self._conexao
                ).buscar_por_id(material_id)

            else:
                atual_id = vinculo["lote_id"]

                if atual_id not in ativos:
                    atual = self._conexao.execute(
                        "SELECT status FROM lotes WHERE id = ?",
                        (atual_id,),
                    ).fetchone()

                    if atual is None or atual["status"] not in (
                        "EM_FORMACAO",
                        "DISPONIVEL",
                    ):
                        raise ValueError(
                            "O vínculo atual deve apontar para um lote ativo."
                        )

                    ativos[atual_id] = self.buscar_por_id(atual_id)

                material = next(
                    (
                        m
                        for m in ativos[atual_id].materiais
                        if str(m.id) == material_id
                    ),
                    None,
                )

                if material is None:
                    raise ValueError(
                        "Material ausente da composição do lote atual."
                    )

            if material is None:
                raise ValueError(
                    "Material da composição não encontrado."
                )

            materiais.append(material)

        return LoteMaterial.reconstituir_encerrado(
            identificador=registro["id"],
            criador=criador,
            dataCriacao=registro["data_criacao"],
            status=registro["status"],
            materiais=materiais,
            pesoRegistrado=registro["peso_registrado"],
        )

    def listar_por_criador(self, usuario):
        registros = self._conexao.execute(
            "SELECT id FROM lotes "
            "WHERE criador_id = ? ORDER BY rowid",
            (str(usuario.id),),
        ).fetchall()

        return [
            self.buscar_por_id(registro["id"])
            for registro in registros
        ]

    def listar_disponiveis(self):
        registros = self._conexao.execute(
            "SELECT id FROM lotes "
            "WHERE status = 'DISPONIVEL' ORDER BY rowid"
        ).fetchall()

        return [
            self.buscar_por_id(registro["id"])
            for registro in registros
        ]