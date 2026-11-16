from math import isfinite


def validar_numero_finito(valor, campo):
    """Exige um número int ou float, sem aceitar booleanos ou infinito."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{campo} deve ser um número.")

    if isinstance(valor, float) and not isfinite(valor):
        raise ValueError(f"{campo} deve ser um número finito.")


def validar_positivo(valor, campo):
    """Exige um número finito maior que zero."""
    validar_numero_finito(valor, campo)

    if valor <= 0:
        raise ValueError(f"{campo} deve ser maior que zero.")


def validar_confianca(valor):
    """Exige uma confiança entre 0 e 1, incluindo os limites."""
    validar_numero_finito(valor, "A confiança")

    if not 0 <= valor <= 1:
        raise ValueError("A confiança deve estar entre 0 e 1.")


def validar_inteiro_positivo(valor, campo):
    """Exige um inteiro maior que zero, sem aceitar booleanos."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(f"{campo} deve ser um número inteiro.")

    if valor <= 0:
        raise ValueError(f"{campo} deve ser maior que zero.")

# Limites operacionais definidos para a versão acadêmica.
PESO_MAXIMO_MATERIAL_KG = 50_000
PESO_MAXIMO_LOTE_KG = 50_000


def validar_peso_material(peso):
    validar_positivo(peso, "O peso do material")

    if peso > PESO_MAXIMO_MATERIAL_KG:
        raise ValueError(
            "O peso de um material não pode ultrapassar 50.000 kg."
        )


def validar_peso_lote(peso):
    validar_positivo(peso, "O peso do lote")

    if peso > PESO_MAXIMO_LOTE_KG:
        raise ValueError(
            "O peso de um lote não pode ultrapassar 50.000 kg."
        )