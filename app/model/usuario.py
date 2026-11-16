from abc import ABC, abstractmethod
from uuid import UUID, uuid4
from datetime import datetime

from werkzeug.security import check_password_hash

from app.model.enums import StatusValidacao
from app.model.material import Material
from app.model.lote import LoteMaterial


class Usuario(ABC):

    def __init__(self, nome, email, senhaHash, telefone, endereco):
        self.__id = uuid4()
        self.__nome = nome
        self.__email = email
        self.__senhaHash = senhaHash
        self.__telefone = telefone
        self.__endereco = endereco
        self.__latitude = None
        self.__longitude = None
        self.__criadoEm = datetime.now()

    @property
    def senhaHash(self):
        """Hash destinado à persistência; não deve ser exibido pela interface."""
        return self.__senhaHash

    @staticmethod
    def reconstituir(
        perfil, identificador, nome, email, senhaHash, telefone,
        endereco, criadoEm, latitude=None, longitude=None,
        cpf=None, cnpj=None, statusValidacao=None,
    ):
        configuracao = PERFIS_USUARIO.get(perfil)

        if configuracao is None:
            raise ValueError("Perfil persistido inválido.")

        classe, documento = configuracao

        argumentos = dict(
            nome=nome,
            email=email,
            senhaHash=senhaHash,
            telefone=telefone,
            endereco=endereco,
        )

        if documento == "cpf":
            if (
                not cpf
                or not cpf.strip()
                or cnpj is not None
                or statusValidacao is not None
            ):
                raise ValueError(
                    "Dados incompatíveis com o perfil catador."
                )

            argumentos["cpf"] = cpf

        elif documento == "cnpj":
            if not cnpj or not cnpj.strip() or cpf is not None:
                raise ValueError(
                    "Dados incompatíveis com o perfil empresarial."
                )

            argumentos["cnpj"] = cnpj
            argumentos["statusValidacao"] = StatusValidacao(
                statusValidacao
            )

        elif any(
            valor is not None
            for valor in (cpf, cnpj, statusValidacao)
        ):
            raise ValueError(
                "Dados incompatíveis com o perfil comum."
            )

        identificador = UUID(str(identificador))
        data = datetime.fromisoformat(criadoEm)

        usuario = classe(**argumentos)
        usuario.__id = identificador
        usuario.__criadoEm = data
        usuario.__latitude = latitude
        usuario.__longitude = longitude

        return usuario


    @abstractmethod
    def atualizarPerfil(self, nome=None, email=None, telefone=None, endereco=None):
        if nome is not None:
            self.__nome = nome

        if email is not None:
            self.__email = email

        if telefone is not None:
            self.__telefone = telefone

        if endereco is not None:
            self.__endereco = endereco
            self.__latitude = None
            self.__longitude = None

    @property
    def id(self):
        return self.__id

    @property
    def nome(self):
        return self.__nome

    @property
    def email(self):
        return self.__email

    @property
    def telefone(self):
        return self.__telefone

    @property
    def endereco(self):
        return self.__endereco

    @property
    def latitude(self):
        return self.__latitude

    @property
    def longitude(self):
        return self.__longitude

    @property
    def criadoEm(self):
        return self.__criadoEm

    def verificarSenha(self, senha):
        return check_password_hash(self.__senhaHash, senha)


class UsuarioComum(Usuario):

    def __init__(self, nome, email, senhaHash, telefone, endereco):
        super().__init__(nome, email, senhaHash, telefone, endereco)

    def atualizarPerfil(self, nome=None, email=None, telefone=None, endereco=None):
        super().atualizarPerfil(nome, email, telefone, endereco)

    def consultarPontosColeta(self, pontos):
        return pontos.copy()

    def identificarResiduo(self, foto, servicoVisao):
        return servicoVisao.identificarResiduo(foto)


class Catador(Usuario):

    def __init__(self, nome, email, senhaHash, telefone, endereco, cpf):
        super().__init__(nome, email, senhaHash, telefone, endereco)
        self.__cpf = cpf

    @property
    def cpf(self):
        return self.__cpf

    def atualizarPerfil(self, nome=None, email=None, telefone=None, endereco=None):
        super().atualizarPerfil(nome, email, telefone, endereco)

    def registrarMaterial(
        self,
        tipoMaterial,
        pesoKg,
        condicaoDeclarada,
        observacoesDeclaradas=None
    ):
        return Material(
            tipoMaterial,
            pesoKg,
            condicaoDeclarada,
            self,
            observacoesDeclaradas
        )

    def criarLote(self, material):
        if material.responsavelAtual is not self:
            raise ValueError(
                "O catador deve ser o responsável atual pelo material."
            )

        return LoteMaterial(self, material)

    def solicitarPrecificacaoMaterial(
        self,
        material,
        horizonteDias,
        servicoPrecificacao
    ):
        return servicoPrecificacao.cotarMaterial(
            material,
            horizonteDias
        )

    def solicitarPrecificacaoLote(
        self,
        lote,
        horizonteDias,
        servicoPrecificacao
    ):
        return servicoPrecificacao.cotarLote(
            lote,
            horizonteDias
        )


class Cooperativa(Usuario):

    def __init__(
        self, nome, email, senhaHash, telefone, endereco, cnpj,
        *, statusValidacao=StatusValidacao.PENDENTE,
    ):
        super().__init__(nome, email, senhaHash, telefone, endereco)
        self.__cnpj = cnpj
        self.__statusValidacao = StatusValidacao(statusValidacao)

    @property
    def cnpj(self):
        return self.__cnpj

    @property
    def statusValidacao(self):
        return self.__statusValidacao

    def atualizarPerfil(self, nome=None, email=None, telefone=None, endereco=None):
        super().atualizarPerfil(nome, email, telefone, endereco)

    def registrarRecebimento(self, material):
        material.transferirResponsabilidade(self)

    def criarLote(self, material):
        if material.responsavelAtual is not self:
            raise ValueError(
                "A cooperativa deve ser a responsável atual pelo material."
            )

        return LoteMaterial(self, material)

    def solicitarPrecificacaoMaterial(
        self,
        material,
        horizonteDias,
        servicoPrecificacao
    ):
        return servicoPrecificacao.cotarMaterial(
            material,
            horizonteDias
        )

    def solicitarPrecificacaoLote(
        self,
        lote,
        horizonteDias,
        servicoPrecificacao
    ):
        return servicoPrecificacao.cotarLote(
            lote,
            horizonteDias
        )


class EmpresaCompradora(Usuario):

    def __init__(
        self, nome, email, senhaHash, telefone, endereco, cnpj,
        *, statusValidacao=StatusValidacao.PENDENTE,
    ):
        super().__init__(nome, email, senhaHash, telefone, endereco)
        self.__cnpj = cnpj
        self.__statusValidacao = StatusValidacao(statusValidacao)

    @property
    def cnpj(self):
        return self.__cnpj

    @property
    def statusValidacao(self):
        return self.__statusValidacao

    def atualizarPerfil(self, nome=None, email=None, telefone=None, endereco=None):
        super().atualizarPerfil(nome, email, telefone, endereco)

    def criarLote(self, material):
        if material.responsavelAtual is not self:
            raise ValueError(
                "A empresa deve ser a responsável atual pelo material."
            )

        return LoteMaterial(self, material)

    def solicitarPrecificacaoMaterial(
        self,
        material,
        horizonteDias,
        servicoPrecificacao
    ):
        return servicoPrecificacao.cotarMaterial(
            material,
            horizonteDias
        )

    def solicitarPrecificacaoLote(
        self,
        lote,
        horizonteDias,
        servicoPrecificacao
    ):
        return servicoPrecificacao.cotarLote(
            lote,
            horizonteDias
        )


class IndustriaTransformadora(Usuario):

    def __init__(
        self, nome, email, senhaHash, telefone, endereco, cnpj,
        *, statusValidacao=StatusValidacao.PENDENTE,
    ):
        super().__init__(nome, email, senhaHash, telefone, endereco)
        self.__cnpj = cnpj
        self.__statusValidacao = StatusValidacao(statusValidacao)

    @property
    def cnpj(self):
        return self.__cnpj

    @property
    def statusValidacao(self):
        return self.__statusValidacao

    def atualizarPerfil(self, nome=None, email=None, telefone=None, endereco=None):
        super().atualizarPerfil(nome, email, telefone, endereco)

    def solicitarPrecificacaoLote(
        self,
        lote,
        horizonteDias,
        servicoPrecificacao
    ):
        return servicoPrecificacao.cotarLote(
            lote,
            horizonteDias
        )

PERFIS_USUARIO = {
    "comum": (UsuarioComum, None),
    "catador": (Catador, "cpf"),
    "cooperativa": (Cooperativa, "cnpj"),
    "empresa": (EmpresaCompradora, "cnpj"),
    "industria": (IndustriaTransformadora, "cnpj"),
}
