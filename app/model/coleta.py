from uuid import uuid4


class HorarioFuncionamento:

    def __init__(self, diaSemana, horaAbertura, horaFechamento):
        if horaAbertura >= horaFechamento:
            raise ValueError(
                "A hora de abertura deve ser anterior à hora de fechamento."
            )

        self.__diaSemana = diaSemana
        self.__horaAbertura = horaAbertura
        self.__horaFechamento = horaFechamento

    @property
    def diaSemana(self):
        return self.__diaSemana

    @property
    def horaAbertura(self):
        return self.__horaAbertura

    @property
    def horaFechamento(self):
        return self.__horaFechamento


class PontoColeta:

    def __init__(self, nome, endereco, latitude, longitude, tipo, tiposAceitos=None, horarios=None):
        self.__id = uuid4()
        self.__nome = nome
        self.__endereco = endereco
        self.__latitude = latitude
        self.__longitude = longitude
        self.__tipo = tipo

        self.__tiposAceitos = list(tiposAceitos) if tiposAceitos is not None else []
        self.__horarios = list(horarios) if horarios is not None else []

    @property
    def id(self):
        return self.__id

    @property
    def nome(self):
        return self.__nome

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
    def tipo(self):
        return self.__tipo

    @property
    def tiposAceitos(self):
        return self.__tiposAceitos.copy()

    @property
    def horarios(self):
        return self.__horarios.copy()

    def aceitaMaterial(self, tipo):
        return tipo in self.__tiposAceitos
