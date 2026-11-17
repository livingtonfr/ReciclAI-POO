import sqlite3

from app.model.comercial import Certificado
from app.model.enums import StatusTransacao


class CertificadoSQLiteDAO:
    """Persiste certificados na transação recebida, sem commit."""

    def __init__(self, conexao):
        self._conexao = conexao

    def buscar_por_id(self, certificado_id):
        registro = self._conexao.execute(
            "SELECT * FROM certificados WHERE id = ?",
            (str(certificado_id),),
        ).fetchone()

        if registro is None:
            return None

        return Certificado.reconstituir(
            registro["id"],
            registro["codigo"],
            registro["data_emissao"],
        )

    def adicionar(self, certificado, transacao=None):
        """Grava o certificado já associado à transação concluída."""
        if transacao is None:
            raise ValueError(
                "A transação do certificado deve ser informada."
            )

        if transacao.certificado is not certificado:
            raise ValueError(
                "O certificado não está associado à transação."
            )

        if transacao.status != StatusTransacao.CONCLUIDA:
            raise ValueError(
                "Certificado só pode ser emitido para transação CONCLUIDA."
            )

        self._conexao.execute("SAVEPOINT adicionar_certificado")

        try:
            registro = self._conexao.execute(
                "SELECT status FROM transacoes WHERE id = ?",
                (str(transacao.id),),
            ).fetchone()

            if registro is None or registro["status"] != "CONCLUIDA":
                raise ValueError(
                    "A transação persistida deve estar CONCLUIDA."
                )

            try:
                self._conexao.execute(
                    "INSERT INTO certificados "
                    "(id, transacao_id, codigo, data_emissao) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        str(certificado.id),
                        str(transacao.id),
                        certificado.codigo,
                        certificado.dataEmissao.isoformat(),
                    ),
                )
            except sqlite3.IntegrityError as erro:
                raise ValueError(
                    "A transação já possui certificado "
                    "ou o código já existe."
                ) from erro

        except Exception:
            self._conexao.execute(
                "ROLLBACK TO SAVEPOINT adicionar_certificado"
            )
            raise
        finally:
            self._conexao.execute(
                "RELEASE SAVEPOINT adicionar_certificado"
            )

        return certificado
