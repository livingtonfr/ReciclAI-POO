from app import app


if __name__ == "__main__":
    app.run(
        debug=app.config["DEBUG"],
        use_reloader=app.config["USE_RELOADER"],
    )