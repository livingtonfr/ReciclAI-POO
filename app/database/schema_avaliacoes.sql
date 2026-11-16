CREATE TABLE IF NOT EXISTS avaliacoes_qualidade (
    id TEXT PRIMARY KEY NOT NULL,

    material_id TEXT NOT NULL REFERENCES materiais(id),

    ordem INTEGER NOT NULL CHECK (
        typeof(ordem) = 'integer' AND ordem >= 0
    ),

    condicao_detectada TEXT NOT NULL CHECK (
        condicao_detectada IN (
            'LIMPO', 'SUJO', 'CONTAMINADO',
            'DANIFICADO', 'NAO_INFORMADO'
        )
    ),

    confianca REAL NOT NULL CHECK (
        confianca >= 0 AND confianca <= 1
    ),

    observacoes TEXT,
    data_avaliacao TEXT NOT NULL,

    UNIQUE (material_id, ordem)
);