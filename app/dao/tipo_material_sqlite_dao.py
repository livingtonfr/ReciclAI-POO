from app.model.material import TipoMaterial


class TipoMaterialSQLiteDAO:
    """Acessa tipos pela conexão recebida, sem confirmar a transação."""

    def __init__(self, conexao):
        self._conexao = conexao

    @staticmethod
    def _converter(registro):
        return TipoMaterial.reconstituir(
            registro["id"],
            registro["nome"],
            registro["descricao"],
            registro["categoria"],
            bool(registro["ativo"]),
        )

    def adicionar(self, tipo):
        self._conexao.execute(
            "INSERT INTO tipos_material "
            "(id, nome, descricao, categoria, ativo) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                str(tipo.id),
                tipo.nome,
                tipo.descricao,
                tipo.categoria.value,
                int(tipo.ativo),
            ),
        )
        return tipo

    def listar(self):
        registros = self._conexao.execute(
            "SELECT id, nome, descricao, categoria, ativo "
            "FROM tipos_material ORDER BY rowid"
        ).fetchall()

        return [
            self._converter(registro)
            for registro in registros
        ]

    def buscar_por_id(self, tipo_id):
        registro = self._conexao.execute(
            "SELECT id, nome, descricao, categoria, ativo "
            "FROM tipos_material WHERE id = ?",
            (str(tipo_id),),
        ).fetchone()

        if registro is None:
            return None

        return self._converter(registro)