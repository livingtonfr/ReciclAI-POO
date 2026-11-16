from app import app
from app.database.contexto import preparar_banco


if __name__ == "__main__":
    caminho = app.config["DATABASE_PATH"]
    preparar_banco(caminho)
    print(f"Banco SQLite: {caminho}")

    app.run(
        debug=app.config["DEBUG"],
        use_reloader=app.config["USE_RELOADER"],
    )
