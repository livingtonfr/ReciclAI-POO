CREATE TABLE IF NOT EXISTS eventos_rastreio (
    id TEXT PRIMARY KEY NOT NULL,

    material_id TEXT NOT NULL REFERENCES materiais(id),

    ordem INTEGER NOT NULL CHECK (
        typeof(ordem) = 'integer' AND ordem >= 0
    ),

    tipo TEXT NOT NULL CHECK (
        tipo IN (
            'REGISTRO', 'AGRUPAMENTO_LOTE',
            'TRANSFERENCIA', 'DESTINACAO'
        )
    ),

    descricao TEXT NOT NULL,
    data_evento TEXT NOT NULL,

    UNIQUE (material_id, ordem)
);