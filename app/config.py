from pathlib import Path


class Config:
    """Configurações da versão acadêmica em desenvolvimento."""

    SECRET_KEY = "reciclai-dev-secret"

    DEBUG = True

    USE_RELOADER = False

    DATABASE_PATH = (
        Path(__file__).resolve().parent.parent
        / "instance"
        / "reciclai.sqlite3"
    )