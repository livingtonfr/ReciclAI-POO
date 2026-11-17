CREATE TABLE IF NOT EXISTS lotes (
    id TEXT PRIMARY KEY NOT NULL,
    criador_id TEXT NOT NULL REFERENCES usuarios(id),
    data_criacao TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('EM_FORMACAO', 'DISPONIVEL', 'NEGOCIADO', 'CANCELADO')
    ),
    peso_registrado REAL CHECK (
        peso_registrado IS NULL
        OR (peso_registrado > 0 AND peso_registrado <= 50000)
    )
);