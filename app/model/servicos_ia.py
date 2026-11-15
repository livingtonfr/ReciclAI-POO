from app.model.material import AvaliacaoQualidade
from app.model.comercial import CotacaoPreco


class ResultadoIdentificacao:

    def __init__(self, tipoMaterial, confianca):
        if confianca < 0 or confianca > 1:
            raise ValueError(
                "A confiança deve estar entre 0 e 1."
            )

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
        if valorPorKgSimulado <= 0:
            raise ValueError(
                "O valor por kg simulado deve ser maior que zero."
            )

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
