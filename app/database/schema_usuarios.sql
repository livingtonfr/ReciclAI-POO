CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY NOT NULL,

    perfil TEXT NOT NULL CHECK (
        perfil IN (
            'comum', 'catador', 'cooperativa',
            'empresa', 'industria'
        )
    ),

    nome TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    senha_hash TEXT NOT NULL,
    telefone TEXT NOT NULL,
    endereco TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    criado_em TEXT NOT NULL,

    cpf TEXT,
    cnpj TEXT,
    status_validacao TEXT,

    CHECK (
        (
            perfil = 'comum'
            AND cpf IS NULL
            AND cnpj IS NULL
            AND status_validacao IS NULL
        )
        OR
        (
            perfil = 'catador'
            AND cpf IS NOT NULL
            AND length(trim(cpf)) > 0
            AND cnpj IS NULL
            AND status_validacao IS NULL
        )
        OR
        (
            perfil IN ('cooperativa', 'empresa', 'industria')
            AND cpf IS NULL
            AND cnpj IS NOT NULL
            AND length(trim(cnpj)) > 0
            AND status_validacao IS NOT NULL
            AND status_validacao IN (
                'PENDENTE', 'APROVADA', 'REJEITADA', 'SUSPENSA'
            )
        )
    )
);