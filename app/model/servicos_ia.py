from app.model.material import AvaliacaoQualidade
from app.model.comercial import CotacaoPreco

from app.model.validacoes import validar_positivo, validar_confianca

class ResultadoIdentificacao:

    def __init__(self, tipoMaterial, confianca):
        validar_confianca(confianca)

        self.__tipoMaterial = tipoMaterial
        self.__confianca = confianca

    @property
    def tipoMaterial(self):
        return self.__tipoMaterial

    @property
    def confianca(self):
        return self.__confianca


class VisaoComputacionalIA:

    def __init__(self, tipoMaterialSimulado, confiancaIdentificacaoSimulada, condicaoSimulada, confiancaAvaliacaoSimulada):
        validar_confianca(confiancaIdentificacaoSimulada)
        validar_confianca(confiancaAvaliacaoSimulada)
        
        self.__tipoMaterialSimulado = tipoMaterialSimulado
        self.__confiancaIdentificacaoSimulada = confiancaIdentificacaoSimulada
        self.__condicaoSimulada = condicaoSimulada
        self.__confiancaAvaliacaoSimulada = confiancaAvaliacaoSimulada

    def identificarResiduo(self, foto):
        return ResultadoIdentificacao(
            self.__tipoMaterialSimulado,
            self.__confiancaIdentificacaoSimulada
        )

    def avaliarMaterial(self, material, foto):
        avaliacao = AvaliacaoQualidade(
            self.__condicaoSimulada,
            self.__confiancaAvaliacaoSimulada,
            "Avaliação simulada por visão computacional."
        )

        material.adicionarAvaliacao(avaliacao)

        return avaliacao


class PrecificacaoIA:

    def __init__(self, valorPorKgSimulado):
        validar_positivo(valorPorKgSimulado, "O valor por kg simulado")

        self.__valorPorKgSimulado = valorPorKgSimulado

    def cotarMaterial(self, material, horizonteDias):
        return CotacaoPreco(
            self.__valorPorKgSimulado,
            horizonteDias,
            material=material
        )

    def cotarLote(self, lote, horizonteDias):
        return CotacaoPreco(
            self.__valorPorKgSimulado,
            horizonteDias,
            lote=lote
        )
