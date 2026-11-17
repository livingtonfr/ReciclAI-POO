CREATE TABLE IF NOT EXISTS materiais (
    id TEXT PRIMARY KEY NOT NULL,

    tipo_material_id TEXT NOT NULL
        REFERENCES tipos_material(id),

    responsavel_atual_id TEXT NOT NULL
        REFERENCES usuarios(id),

    peso_kg REAL NOT NULL
        CHECK (peso_kg > 0 AND peso_kg <= 50000),

    condicao_declarada TEXT NOT NULL CHECK (
        condicao_declarada IN (
            'LIMPO', 'SUJO', 'CONTAMINADO',
            'DANIFICADO', 'NAO_INFORMADO'
        )
    ),

    observacoes_declaradas TEXT,

    status TEXT NOT NULL CHECK (
        status IN (
            'REGISTRADO', 'DISPONIVEL', 'EM_LOTE', 'DESTINADO'
        )
    ),

    data_registro TEXT NOT NULL
);