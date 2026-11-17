from uuid import UUID, uuid4
from datetime import datetime

from app.model.validacoes import validar_positivo
from app.model.validacoes import validar_peso_lote
from app.model.enums import StatusLote, StatusMaterial, StatusTransacao


class LoteMaterial:

    def __init__(self, criador, materialInicial):
        from app.model.usuario import (
            Catador,
            Cooperativa,
            EmpresaCompradora,
        )

        if not isinstance(
            criador,
            (Catador, Cooperativa, EmpresaCompradora),
        ):
            raise ValueError(
                "Somente catadores, cooperativas e empresas "
                "compradoras podem criar lotes."
            )

        if materialInicial.status != StatusMaterial.DISPONIVEL:
            raise ValueError("O material inicial deve estar DISPONIVEL.")

        if materialInicial.responsavelAtual is not criador:
            raise ValueError("O criador deve ser o responsável atual pelo material inicial.")

        self.__id = uuid4()
        self.__dataCriacao = datetime.now()
        self.__status = StatusLote.EM_FORMACAO
        self.__criador = criador
        self.__materiais = []
        self.__transacoes = []
        self.__pesoRegistrado = None

        self.adicionarMaterial(materialInicial)

    @classmethod
    def reconstituir_encerrado(
        cls,
        identificador,
        criador,
        dataCriacao,
        status,
        materiais,
        pesoRegistrado=None,
    ):
        """Restaura a composição de lote encerrado sem reagrupar materiais."""
        from app.model.material import Material
        from app.model.usuario import (
            Catador,
            Cooperativa,
            EmpresaCompradora,
        )

        identificador = UUID(str(identificador))
        estado = StatusLote(status)
        data = datetime.fromisoformat(dataCriacao)

        if estado not in (StatusLote.NEGOCIADO, StatusLote.CANCELADO):
            raise ValueError(
                "Este método restaura somente lotes encerrados."
            )

        if not isinstance(
            criador,
            (Catador, Cooperativa, EmpresaCompradora),
        ):
            raise ValueError("Perfil de criador inválido.")

        materiais = list(materiais)

        if not materiais or not all(
            isinstance(m, Material) for m in materiais
        ):
            raise ValueError(
                "A composição deve conter materiais válidos."
            )

        if len({m.id for m in materiais}) != len(materiais):
            raise ValueError(
                "A composição contém material repetido."
            )

        if len({m.tipoMaterial.id for m in materiais}) != 1:
            raise ValueError(
                "Os materiais devem possuir o mesmo tipo."
            )

        validar_peso_lote(sum(m.pesoKg for m in materiais))

        if pesoRegistrado is not None:
            validar_peso_lote(pesoRegistrado)

        if any(
            m.loteAtual is not None
            and m.loteAtual.id == identificador
            for m in materiais
        ):
            raise ValueError(
                "Lote encerrado não pode manter vínculo atual."
            )

        lote = cls.__new__(cls)
        lote.__id = identificador
        lote.__criador = criador
        lote.__dataCriacao = data
        lote.__status = estado
        lote.__materiais = materiais
        lote.__pesoRegistrado = pesoRegistrado
        lote.__transacoes = []
        return lote

    @classmethod
    def reconstituir_ativo(
        cls,
        identificador,
        criador,
        dataCriacao,
        status,
        dadosMateriais,
        pesoRegistrado=None,
    ):
        """Restaura lote e materiais juntos, sem eventos novos."""
        from app.model.material import Material
        from app.model.usuario import (
            Catador,
            Cooperativa,
            EmpresaCompradora,
        )

        identificador = UUID(str(identificador))
        estado = StatusLote(status)
        data = datetime.fromisoformat(dataCriacao)

        if estado not in (
            StatusLote.EM_FORMACAO,
            StatusLote.DISPONIVEL,
        ):
            raise ValueError(
                "Este método restaura somente lotes ativos."
            )

        if not isinstance(
            criador,
            (Catador, Cooperativa, EmpresaCompradora),
        ):
            raise ValueError("Perfil de criador inválido.")

        if pesoRegistrado is not None:
            validar_peso_lote(pesoRegistrado)

        lote = cls.__new__(cls)
        lote.__id = identificador
        lote.__criador = criador
        lote.__dataCriacao = data
        lote.__status = estado
        lote.__pesoRegistrado = pesoRegistrado
        lote.__materiais = []
        lote.__transacoes = []

        materiais = [
            Material._reconstituir_em_lote(lote, **dados)
            for dados in dadosMateriais
        ]

        if not materiais:
            raise ValueError(
                "O lote não pode ficar sem materiais."
            )

        if len({m.id for m in materiais}) != len(materiais):
            raise ValueError(
                "A composição contém material repetido."
            )

        tipo = materiais[0].tipoMaterial

        if any(m.tipoMaterial is not tipo for m in materiais):
            raise ValueError(
                "Os materiais devem compartilhar a instância do tipo."
            )

        validar_peso_lote(
            sum(m.pesoKg for m in materiais)
        )

        lote.__materiais = materiais
        return lote

    @property
    def id(self):
        return self.__id

    @property
    def dataCriacao(self):
        return self.__dataCriacao

    @property
    def status(self):
        return self.__status

    @property
    def criador(self):
        return self.__criador

    @property
    def pesoRegistrado(self):
        return self.__pesoRegistrado

    @property
    def materiais(self):
        return self.__materiais.copy()

    @property
    def transacoes(self):
        return self.__transacoes.copy()

    def adicionarMaterial(self, material):
        if self.__status != StatusLote.EM_FORMACAO:
            raise ValueError("Materiais só podem ser adicionados enquanto o lote estiver EM_FORMACAO.")

        if material.status != StatusMaterial.DISPONIVEL:
            raise ValueError("Somente material DISPONIVEL pode ser adicionado ao lote.")

        if material.responsavelAtual is not self.__criador:
            raise ValueError("O material deve estar sob responsabilidade do criador do lote.")

        if len(self.__materiais) > 0:
            tipo_lote = self.__materiais[0].tipoMaterial

            if material.tipoMaterial is not tipo_lote:
                raise ValueError("Todos os materiais do lote devem possuir o mesmo TipoMaterial.")

        peso_apos_adicao = (
            self.calcularPesoTotal() + material.pesoKg
        )
        validar_peso_lote(peso_apos_adicao)

        material.agruparEmLote(self)
        self.__materiais.append(material)

        # A composição mudou; a pesagem anterior deixou de ser válida.
        self.__pesoRegistrado = None

    def removerMaterial(self, material):
        if self.__status != StatusLote.EM_FORMACAO:
            raise ValueError("Materiais só podem ser removidos enquanto o lote estiver EM_FORMACAO.")

        if material not in self.__materiais:
            raise ValueError("O material não pertence a este lote.")

        if len(self.__materiais) == 1:
            raise ValueError("O lote não pode ficar sem materiais.")

        material.removerDoLote(self)
        self.__materiais.remove(material)

        # A composição mudou; a pesagem anterior deixou de ser válida.
        self.__pesoRegistrado = None

    def calcularPesoTotal(self):
        return sum(material.pesoKg for material in self.__materiais)

    def disponibilizar(self):
        if self.__status != StatusLote.EM_FORMACAO:
            raise ValueError("Somente lote EM_FORMACAO pode ser disponibilizado.")

        self.__status = StatusLote.DISPONIVEL

    def registrarPesagem(self, peso):
        if self.__status in (StatusLote.NEGOCIADO, StatusLote.CANCELADO):
            raise ValueError("Não é possível registrar pesagem em lote encerrado.")

        validar_peso_lote(peso)

        self.__pesoRegistrado = peso

    def restaurar_transacoes(self, transacoes):
        """Associa o histórico reconstruído sem executar operações comerciais."""
        from app.model.comercial import Transacao

        if self.__transacoes:
            raise ValueError(
                "O lote já possui transações carregadas."
            )

        transacoes = list(transacoes)

        if not all(isinstance(t, Transacao) for t in transacoes):
            raise ValueError(
                "A lista deve conter somente transações."
            )

        if len({t.id for t in transacoes}) != len(transacoes):
            raise ValueError(
                "A lista contém transações repetidas."
            )

        if any(t.lote is not self for t in transacoes):
            raise ValueError(
                "Todas as transações devem apontar para este lote."
            )

        concluidas = sum(
            t.status == StatusTransacao.CONCLUIDA
            for t in transacoes
        )

        if self.__status == StatusLote.NEGOCIADO:
            if concluidas != 1:
                raise ValueError(
                    "Lote NEGOCIADO deve possuir uma transação concluída."
                )
        elif concluidas:
            raise ValueError(
                "Somente lote NEGOCIADO pode possuir transação concluída."
            )

        if self.__status == StatusLote.EM_FORMACAO and transacoes:
            raise ValueError(
                "Lote EM_FORMACAO não pode possuir transações."
            )

        if self.__status != StatusLote.DISPONIVEL:
            if any(
                t.status == StatusTransacao.PENDENTE
                for t in transacoes
            ):
                raise ValueError(
                    "Transações pendentes exigem lote DISPONIVEL."
                )

        self.__transacoes = transacoes

    def adicionarTransacao(self, transacao):
        self.__transacoes.append(transacao)

    def possuiTransacaoConcluida(self):
        return any(
            transacao.status == StatusTransacao.CONCLUIDA
            for transacao in self.__transacoes
        )

    def marcarComoNegociado(self):
        if self.__status != StatusLote.DISPONIVEL:
            raise ValueError("Somente lote DISPONIVEL pode ser marcado como NEGOCIADO.")

        self.__status = StatusLote.NEGOCIADO

    def cancelar(self):
        if self.__status not in (StatusLote.EM_FORMACAO, StatusLote.DISPONIVEL):
            raise ValueError(
                "Somente lote EM_FORMACAO ou DISPONIVEL pode ser cancelado."
            )

        for material in self.__materiais:
            material._liberarDoLote()

        for transacao in self.__transacoes:
            if transacao.status == StatusTransacao.PENDENTE:
                transacao.cancelar()

        self.__status = StatusLote.CANCELADO
