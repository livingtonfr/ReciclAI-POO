from uuid import UUID, uuid4
from datetime import datetime

from app.model.validacoes import validar_positivo, validar_inteiro_positivo, validar_peso_lote
from app.model.enums import StatusLote, StatusTransacao, StatusMaterial
from app.model.usuario import Catador, Cooperativa, EmpresaCompradora, IndustriaTransformadora


class CotacaoPreco:

    def __init__(self, valorPorKg, horizonteDias, material=None, lote=None):

        validar_positivo(valorPorKg, "O valor por kg")
        validar_inteiro_positivo(horizonteDias, "O horizonte em dias")

        if (material is None) == (lote is None):
            raise ValueError("A cotação deve referenciar exatamente um Material ou um LoteMaterial.")

        self.__id = uuid4()
        self.__valorPorKg = valorPorKg
        self.__horizonteDias = horizonteDias
        self.__dataCotacao = datetime.now()
        self.__material = material
        self.__lote = lote

    @property
    def id(self):
        return self.__id

    @property
    def valorPorKg(self):
        return self.__valorPorKg

    @property
    def horizonteDias(self):
        return self.__horizonteDias

    @property
    def dataCotacao(self):
        return self.__dataCotacao

    @property
    def material(self):
        return self.__material

    @property
    def lote(self):
        return self.__lote


class Transacao:

    def __init__(self, lote, vendedor, comprador, valorTotal):
        validar_positivo(valorTotal, "O valor total")

        if vendedor is comprador or vendedor.id == comprador.id:
            raise ValueError("Vendedor e comprador devem ser usuários distintos.")

        if vendedor is not lote.criador:
            raise ValueError("O vendedor deve ser o criador do lote.")

        if not isinstance(vendedor, (Catador, Cooperativa, EmpresaCompradora)):
            raise ValueError("Usuário não elegível como vendedor.")

        if not isinstance(comprador, (Cooperativa, EmpresaCompradora, IndustriaTransformadora)):
            raise ValueError("Usuário não elegível como comprador.")

        if lote.status != StatusLote.DISPONIVEL:
            raise ValueError("Somente lote DISPONIVEL pode ser negociado.")

        if lote.possuiTransacaoConcluida():
            raise ValueError("O lote já possui uma transação concluída.")

        self.__id = uuid4()
        self.__lote = lote
        self.__vendedor = vendedor
        self.__comprador = comprador
        self.__valorTotal = valorTotal
        self.__dataTransacao = datetime.now()
        self.__status = StatusTransacao.PENDENTE
        self.__pesoNegociado = None
        self.__certificado = None

        lote.adicionarTransacao(self)

    @classmethod
    def reconstituir(
        cls,
        identificador,
        lote,
        vendedor,
        comprador,
        valorTotal,
        dataTransacao,
        status,
        pesoNegociado=None,
        certificado=None,
    ):
        """Recupera dados sem registrar proposta ou executar negociação."""
        from app.model.lote import LoteMaterial

        identificador = UUID(str(identificador))
        data = datetime.fromisoformat(dataTransacao)
        estado = StatusTransacao(status)

        if not isinstance(lote, LoteMaterial):
            raise ValueError("Lote inválido.")

        if not isinstance(
            vendedor,
            (Catador, Cooperativa, EmpresaCompradora),
        ):
            raise ValueError("Perfil de vendedor inválido.")

        if not isinstance(
            comprador,
            (Cooperativa, EmpresaCompradora, IndustriaTransformadora),
        ):
            raise ValueError("Perfil de comprador inválido.")

        if vendedor.id == comprador.id:
            raise ValueError(
                "Vendedor e comprador devem ser usuários distintos."
            )

        if vendedor is not lote.criador:
            raise ValueError(
                "Use a instância do criador do lote como vendedor."
            )

        validar_positivo(valorTotal, "O valor total")

        if estado == StatusTransacao.CONCLUIDA:
            validar_peso_lote(pesoNegociado)

            if lote.status != StatusLote.NEGOCIADO:
                raise ValueError(
                    "Transação concluída exige lote NEGOCIADO."
                )
        else:
            if pesoNegociado is not None:
                raise ValueError(
                    "Somente transação concluída possui peso negociado."
                )

        if estado == StatusTransacao.PENDENTE:
            if lote.status != StatusLote.DISPONIVEL:
                raise ValueError(
                    "Transação pendente exige lote DISPONIVEL."
                )

        if estado == StatusTransacao.CANCELADA:
            if lote.status not in (
                StatusLote.DISPONIVEL,
                StatusLote.NEGOCIADO,
                StatusLote.CANCELADO,
            ):
                raise ValueError(
                    "Estado do lote incompatível com transação cancelada."
                )

        if certificado is not None:
            if not isinstance(certificado, Certificado):
                raise ValueError("Certificado inválido.")

            if estado != StatusTransacao.CONCLUIDA:
                raise ValueError(
                    "Certificado exige transação concluída."
                )

        transacao = cls.__new__(cls)
        transacao.__id = identificador
        transacao.__lote = lote
        transacao.__vendedor = vendedor
        transacao.__comprador = comprador
        transacao.__valorTotal = valorTotal
        transacao.__dataTransacao = data
        transacao.__status = estado
        transacao.__pesoNegociado = pesoNegociado
        transacao.__certificado = certificado

        return transacao

    @property
    def id(self):
        return self.__id

    @property
    def lote(self):
        return self.__lote

    @property
    def vendedor(self):
        return self.__vendedor

    @property
    def comprador(self):
        return self.__comprador

    @property
    def valorTotal(self):
        return self.__valorTotal

    @property
    def dataTransacao(self):
        return self.__dataTransacao

    @property
    def status(self):
        return self.__status

    @property
    def pesoNegociado(self):
        return self.__pesoNegociado

    @property
    def certificado(self):
        return self.__certificado

    def cancelar(self):
        if self.__status != StatusTransacao.PENDENTE:
            raise ValueError("Somente transação PENDENTE pode ser cancelada.")

        self.__status = StatusTransacao.CANCELADA

    def concluir(self):
        # Validações antes de qualquer alteração
        if self.__status != StatusTransacao.PENDENTE:
            raise ValueError("Somente transação PENDENTE pode ser concluída.")

        if self.__lote.status != StatusLote.DISPONIVEL:
            raise ValueError("O lote deve estar DISPONIVEL para concluir a transação.")

        if self.__lote.possuiTransacaoConcluida():
            raise ValueError("O lote já possui uma transação concluída.")

        if self.__vendedor is not self.__lote.criador:
            raise ValueError("O vendedor deve ser o criador do lote.")

        # Confere todos os materiais antes de alterar qualquer um.
        for material in self.__lote.materiais:
            if material.responsavelAtual is not self.__vendedor:
                raise ValueError(
                    "Todos os materiais devem continuar "
                    "sob responsabilidade do vendedor."
                )

            if (
                material.status != StatusMaterial.EM_LOTE
                or material.loteAtual is not self.__lote
            ):
                raise ValueError(
                    "Todos os materiais devem continuar "
                    "vinculados ao lote negociado."
                )
            
        # Define o peso comercial da negociação
        if self.__lote.pesoRegistrado is not None:
            peso_negociado = self.__lote.pesoRegistrado
        else:
            peso_negociado = self.__lote.calcularPesoTotal()

        validar_peso_lote(peso_negociado)

        # A partir daqui começam as alterações
        self.__pesoNegociado = peso_negociado

        for material in self.__lote.materiais:
            material.transferirResponsabilidade(self.__comprador)

            if isinstance(self.__comprador, IndustriaTransformadora):
                material.destinar()
            else:
                material._liberarDoLote()

        self.__lote.marcarComoNegociado()

        for outra_transacao in self.__lote.transacoes:
            if (
                outra_transacao is not self
                and outra_transacao.status == StatusTransacao.PENDENTE
            ):
                outra_transacao.cancelar()

        self.__status = StatusTransacao.CONCLUIDA

    def associarCertificado(self, certificado):
        if self.__status != StatusTransacao.CONCLUIDA:
            raise ValueError(
                "Certificado só pode ser associado a transação CONCLUIDA."
            )

        if self.__certificado is not None:
            raise ValueError(
                "A transação já possui um certificado."
            )

        self.__certificado = certificado


class Certificado:

    def __init__(self, codigo):
        self.__id = uuid4()
        self.__codigo = codigo
        self.__dataEmissao = datetime.now()

    @classmethod
    def reconstituir(cls, identificador, codigo, dataEmissao):
        """Recupera um certificado sem gerar novo ID ou data."""
        identificador = UUID(str(identificador))
        data = datetime.fromisoformat(dataEmissao)

        if not isinstance(codigo, str) or not codigo.strip():
            raise ValueError(
                "O código do certificado deve ser preenchido."
            )

        certificado = cls.__new__(cls)
        certificado.__id = identificador
        certificado.__codigo = codigo
        certificado.__dataEmissao = data

        return certificado

    @property
    def id(self):
        return self.__id

    @property
    def codigo(self):
        return self.__codigo

    @property
    def dataEmissao(self):
        return self.__dataEmissao

    def gerarPDF(self):
        """Exibe uma simulação textual; não cria arquivo PDF.

        Na interface web, a impressão e o salvamento em PDF
        são realizados pelo navegador, via window.print().
        """
        print(
            f"Simulação do certificado {self.__codigo}: "
            "nenhum arquivo PDF foi gerado. "
            "Na aplicação web, use o botão de impressão "
            "para imprimir ou salvar em PDF."
        )
