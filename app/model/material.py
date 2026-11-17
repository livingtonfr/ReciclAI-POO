from uuid import UUID, uuid4
from datetime import datetime

from app.model.validacoes import validar_positivo, validar_confianca
from app.model.validacoes import validar_peso_material
from app.model.enums import CategoriaMaterial, CondicaoMaterial, StatusMaterial, TipoEventoRastreio


class TipoMaterial:

    def __init__(self, nome, descricao, categoria):
        self.__id = uuid4()
        self.__nome = nome
        self.__descricao = descricao
        self.__categoria = categoria
        self.__ativo = True

    @classmethod
    def reconstituir(
        cls, identificador, nome, descricao, categoria, ativo
    ):
        """Reconstrói um tipo persistido, preservando seu identificador."""
        identificador = UUID(str(identificador))
        categoria = CategoriaMaterial(categoria)

        if not isinstance(ativo, bool):
            raise ValueError("O estado ativo deve ser booleano.")

        tipo = cls(nome, descricao, categoria)
        tipo.__id = identificador
        tipo.__ativo = ativo
        return tipo

    @property
    def id(self):
        return self.__id

    @property
    def nome(self):
        return self.__nome

    @property
    def descricao(self):
        return self.__descricao

    @property
    def categoria(self):
        return self.__categoria

    @property
    def ativo(self):
        return self.__ativo


class EventoRastreio:

    def __init__(self, tipo, descricao):
        self.__id = uuid4()
        self.__tipo = tipo
        self.__dataEvento = datetime.now()
        self.__descricao = descricao

    @classmethod
    def reconstituir(cls, identificador, tipo, descricao, dataEvento):
        identificador = UUID(str(identificador))
        tipo = TipoEventoRastreio(tipo)
        data = datetime.fromisoformat(dataEvento)

        evento = cls.__new__(cls)
        evento.__id = identificador
        evento.__tipo = tipo
        evento.__descricao = descricao
        evento.__dataEvento = data
        return evento

    @property
    def id(self):
        return self.__id

    @property
    def tipo(self):
        return self.__tipo

    @property
    def dataEvento(self):
        return self.__dataEvento

    @property
    def descricao(self):
        return self.__descricao


class AvaliacaoQualidade:

    def __init__(self, condicaoDetectada, confianca, observacoes=None):
        validar_confianca(confianca)

        self.__id = uuid4()
        self.__condicaoDetectada = condicaoDetectada
        self.__confianca = confianca
        self.__observacoes = observacoes
        self.__dataAvaliacao = datetime.now()

    @classmethod
    def reconstituir(
        cls,
        identificador,
        condicaoDetectada,
        confianca,
        dataAvaliacao,
        observacoes=None,
    ):
        validar_confianca(confianca)
        identificador = UUID(str(identificador))
        condicao = CondicaoMaterial(condicaoDetectada)
        data = datetime.fromisoformat(dataAvaliacao)

        avaliacao = cls.__new__(cls)
        avaliacao.__id = identificador
        avaliacao.__condicaoDetectada = condicao
        avaliacao.__confianca = confianca
        avaliacao.__dataAvaliacao = data
        avaliacao.__observacoes = observacoes
        return avaliacao

    @property
    def id(self):
        return self.__id

    @property
    def condicaoDetectada(self):
        return self.__condicaoDetectada

    @property
    def confianca(self):
        return self.__confianca

    @property
    def observacoes(self):
        return self.__observacoes

    @property
    def dataAvaliacao(self):
        return self.__dataAvaliacao


class Material:

    def __init__(self, tipoMaterial, pesoKg, condicaoDeclarada, responsavelAtual, observacoesDeclaradas=None):
        validar_peso_material(pesoKg)

        self.__id = uuid4()
        self.__tipoMaterial = tipoMaterial
        self.__pesoKg = pesoKg
        self.__condicaoDeclarada = condicaoDeclarada
        self.__observacoesDeclaradas = observacoesDeclaradas
        self.__status = StatusMaterial.REGISTRADO
        self.__dataRegistro = datetime.now()
        self.__responsavelAtual = responsavelAtual
        self.__loteAtual = None
        self.__avaliacoes = []
        self.__eventos = []

        evento_registro = EventoRastreio(
            TipoEventoRastreio.REGISTRO,
            "Material registrado na plataforma."
        )

        self.adicionarEvento(evento_registro)

    @classmethod
    def reconstituir(
        cls,
        identificador,
        tipoMaterial,
        pesoKg,
        condicaoDeclarada,
        responsavelAtual,
        status,
        dataRegistro,
        eventos,
        avaliacoes,
        observacoesDeclaradas=None,
    ):
        """Restaura um material sem executar operações de negócio."""
        from app.model.usuario import Usuario

        validar_peso_material(pesoKg)
        identificador = UUID(str(identificador))
        condicao = CondicaoMaterial(condicaoDeclarada)
        estado = StatusMaterial(status)
        data = datetime.fromisoformat(dataRegistro)

        if estado == StatusMaterial.EM_LOTE:
            raise ValueError(
                "A reconstrução de material EM_LOTE depende "
                "da persistência de lotes, ainda não implementada."
            )

        if not isinstance(tipoMaterial, TipoMaterial):
            raise TypeError("Tipo de material inválido.")

        if not isinstance(responsavelAtual, Usuario):
            raise TypeError("Responsável inválido.")

        eventos = list(eventos)
        avaliacoes = list(avaliacoes)

        if not all(isinstance(item, EventoRastreio) for item in eventos):
            raise TypeError("Histórico contém elemento inválido.")

        if not all(
            isinstance(item, AvaliacaoQualidade)
            for item in avaliacoes
        ):
            raise TypeError("Avaliações contêm elemento inválido.")

        material = cls.__new__(cls)
        material.__id = identificador
        material.__tipoMaterial = tipoMaterial
        material.__pesoKg = pesoKg
        material.__condicaoDeclarada = condicao
        material.__observacoesDeclaradas = observacoesDeclaradas
        material.__status = estado
        material.__dataRegistro = data
        material.__responsavelAtual = responsavelAtual
        material.__loteAtual = None
        material.__eventos = eventos
        material.__avaliacoes = avaliacoes
        return material

    @classmethod
    def _reconstituir_em_lote(cls, lote, **dados):
        """Uso interno da reconstrução de lotes ativos."""
        from app.model.lote import LoteMaterial
        from app.model.enums import StatusLote

        if not isinstance(lote, LoteMaterial) or lote.status not in (
            StatusLote.EM_FORMACAO,
            StatusLote.DISPONIVEL,
        ):
            raise ValueError("O vínculo exige um lote ativo.")

        if StatusMaterial(dados["status"]) != StatusMaterial.EM_LOTE:
            raise ValueError(
                "O material vinculado deve estar EM_LOTE."
            )

        if dados["responsavelAtual"] is not lote.criador:
            raise ValueError(
                "O responsável deve ser a instância do criador do lote."
            )

        material = cls.reconstituir(
            **(dados | {"status": "DISPONIVEL"})
        )
        material.__status = StatusMaterial.EM_LOTE
        material.__loteAtual = lote
        return material

    @property
    def id(self):
        return self.__id

    @property
    def tipoMaterial(self):
        return self.__tipoMaterial

    @property
    def pesoKg(self):
        return self.__pesoKg

    @property
    def condicaoDeclarada(self):
        return self.__condicaoDeclarada

    @property
    def observacoesDeclaradas(self):
        return self.__observacoesDeclaradas

    @property
    def status(self):
        return self.__status

    @property
    def dataRegistro(self):
        return self.__dataRegistro

    @property
    def responsavelAtual(self):
        return self.__responsavelAtual

    @property
    def loteAtual(self):
        return self.__loteAtual

    def obterHistorico(self):
        return self.__eventos.copy()

    def adicionarEvento(self, evento):
        self.__eventos.append(evento)

    def disponibilizar(self):
        if self.__status != StatusMaterial.REGISTRADO:
            raise ValueError(
                "Somente material REGISTRADO pode ser disponibilizado."
            )

        self.__status = StatusMaterial.DISPONIVEL

    def transferirResponsabilidade(self, novoResponsavel):
        self.__responsavelAtual = novoResponsavel

        evento = EventoRastreio(
            TipoEventoRastreio.TRANSFERENCIA,
            "Responsabilidade do material transferida."
        )

        self.adicionarEvento(evento)

    def destinar(self):
        self.__loteAtual = None
        self.__status = StatusMaterial.DESTINADO

        evento = EventoRastreio(
            TipoEventoRastreio.DESTINACAO,
            "Material destinado."
        )

        self.adicionarEvento(evento)

    def adicionarAvaliacao(self, avaliacao):
        if not isinstance(avaliacao, AvaliacaoQualidade):
            raise TypeError(
                "A avaliação deve ser uma instância de AvaliacaoQualidade."
            )

        self.__avaliacoes.append(avaliacao)

    def obterAvaliacoes(self):
        return self.__avaliacoes.copy()

    def agruparEmLote(self, lote):
        if self.__status != StatusMaterial.DISPONIVEL:
            raise ValueError(
                "Somente material DISPONIVEL pode entrar em um lote."
            )

        if self.__loteAtual is not None:
            raise ValueError(
                "O material já pertence a um lote."
            )

        self.__loteAtual = lote
        self.__status = StatusMaterial.EM_LOTE

        evento = EventoRastreio(
            TipoEventoRastreio.AGRUPAMENTO_LOTE,
            "Material agrupado em lote."
        )

        self.adicionarEvento(evento)

    def removerDoLote(self, lote):
        if self.__status != StatusMaterial.EM_LOTE:
            raise ValueError(
                "O material não está em lote."
            )

        if self.__loteAtual is not lote:
            raise ValueError(
                "O material não pertence ao lote informado."
            )

        self.__loteAtual = None
        self.__status = StatusMaterial.DISPONIVEL

    def _liberarDoLote(self):
        self.__loteAtual = None
        self.__status = StatusMaterial.DISPONIVEL
