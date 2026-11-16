class CertificadoDAO:
    """Armazena e consulta certificados em memória."""

    def __init__(self, repositorio):
        self._repositorio = repositorio

    def buscar_por_id(self, certificado_id):
        for certificado in self._repositorio.certificados:
            if str(certificado.id) == str(certificado_id):
                return certificado

        return None

    def adicionar(self, certificado):
        if self.buscar_por_id(certificado.id) is not None:
            raise ValueError("O certificado já está cadastrado.")

        self._repositorio.certificados.append(certificado)
        return certificado