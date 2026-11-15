from uuid import uuid4
from datetime import datetime

from app.model.enums import StatusLote, StatusMaterial, StatusTransacao


class LoteMaterial:

    def __init__(self, criador, materialInicial):
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

        self.__materiais.append(material)
        material.agruparEmLote(self)

    def removerMaterial(self, material):
        if self.__status != StatusLote.EM_FORMACAO:
            raise ValueError("Materiais só podem ser removidos enquanto o lote estiver EM_FORMACAO.")

        if material not in self.__materiais:
            raise ValueError("O material não pertence a este lote.")

        if len(self.__materiais) == 1:
            raise ValueError("O lote não pode ficar sem materiais.")

        self.__materiais.remove(material)
        material.removerDoLote(self)

    def calcularPesoTotal(self):
        return sum(material.pesoKg for material in self.__materiais)

    def disponibilizar(self):
        if self.__status != StatusLote.EM_FORMACAO:
            raise ValueError("Somente lote EM_FORMACAO pode ser disponibilizado.")

        self.__status = StatusLote.DISPONIVEL

    def registrarPesagem(self, peso):
        if self.__status in (StatusLote.NEGOCIADO, StatusLote.CANCELADO):
            raise ValueError("Não é possível registrar pesagem em lote encerrado.")

        if peso <= 0:
            raise ValueError("A pesagem deve ser maior que zero.")

        self.__pesoRegistrado = peso

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
