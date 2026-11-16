CREATE TABLE IF NOT EXISTS transacoes (
    id TEXT PRIMARY KEY NOT NULL,
    lote_id TEXT NOT NULL REFERENCES lotes(id),
    vendedor_id TEXT NOT NULL REFERENCES usuarios(id),
    comprador_id TEXT NOT NULL REFERENCES usuarios(id),
    valor_total REAL NOT NULL CHECK (
        typeof(valor_total) IN ('integer', 'real')
        AND valor_total > 0
        AND valor_total <= 1.7976931348623157e308
    ),
    data_transacao TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('PENDENTE', 'CONCLUIDA', 'CANCELADA')
    ),
    peso_negociado REAL,

    CHECK (vendedor_id <> comprador_id),

    CHECK (
        (
            status = 'CONCLUIDA'
            AND peso_negociado IS NOT NULL
            AND typeof(peso_negociado) IN ('integer', 'real')
            AND peso_negociado > 0
            AND peso_negociado <= 50000
        )
        OR
        (
            status IN ('PENDENTE', 'CANCELADA')
            AND peso_negociado IS NULL
        )
    )
);