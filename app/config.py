import os
from pathlib import Path


class Config:
    """Configurações da versão acadêmica em desenvolvimento."""

    SECRET_KEY = os.environ.get("RECICLAI_SECRET_KEY", "reciclai-dev-secret")

    DEBUG = True

    USE_RELOADER = False

    # O banco pode ser movido (por exemplo, para fora do OneDrive) com a
    # variável de ambiente RECICLAI_DB.
    DATABASE_PATH = Path(
        os.environ.get("RECICLAI_DB")
        or (
            Path(__file__).resolve().parent.parent
            / "instance"
            / "reciclai.sqlite3"
        )
    )

    # O reset apaga TODOS os dados do banco; fica desligado por padrão.
    # Para habilitar: $env:RECICLAI_PERMITIR_RESET = "1"
    PERMITIR_RESET_DEMO = os.environ.get("RECICLAI_PERMITIR_RESET") == "1"
