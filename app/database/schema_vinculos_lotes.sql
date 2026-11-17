CREATE TABLE IF NOT EXISTS vinculos_lotes_atuais (
    material_id TEXT PRIMARY KEY NOT NULL,
    lote_id TEXT NOT NULL,
    FOREIGN KEY (lote_id, material_id)
        REFERENCES lotes_materiais(lote_id, material_id)
);