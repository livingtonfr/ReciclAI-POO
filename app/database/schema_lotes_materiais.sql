CREATE TABLE IF NOT EXISTS lotes_materiais (
    lote_id TEXT NOT NULL REFERENCES lotes(id),
    material_id TEXT NOT NULL REFERENCES materiais(id),
    ordem INTEGER NOT NULL CHECK (
        typeof(ordem) = 'integer' AND ordem >= 0
    ),
    PRIMARY KEY (lote_id, material_id),
    UNIQUE (lote_id, ordem)
);