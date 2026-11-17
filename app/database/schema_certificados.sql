CREATE TABLE IF NOT EXISTS certificados (
    id TEXT PRIMARY KEY NOT NULL,
    transacao_id TEXT NOT NULL UNIQUE REFERENCES transacoes(id),
    codigo TEXT NOT NULL UNIQUE CHECK (
        length(trim(codigo)) > 0
    ),
    data_emissao TEXT NOT NULL
);