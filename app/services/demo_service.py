class ResetDemoNegadoError(PermissionError):
    """A reinicialização da demonstração não está permitida."""


class DemoService:
    def __init__(self, reinicializar):
        self._reinicializar = reinicializar

    def resetar(self, usuario, modo_desenvolvimento):
        if usuario is None or not modo_desenvolvimento:
            raise ResetDemoNegadoError(
                "A reinicialização da demonstração "
                "não está permitida."
            )

        self._reinicializar()