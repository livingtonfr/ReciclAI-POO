CREATE TABLE IF NOT EXISTS tipos_material (
    id TEXT PRIMARY KEY NOT NULL,
    nome TEXT NOT NULL,
    descricao TEXT NOT NULL,
    categoria TEXT NOT NULL CHECK (
        categoria IN (
            'PLASTICO', 'PAPEL', 'VIDRO', 'METAL',
            'ORGANICO', 'ELETRONICO', 'PERIGOSO', 'REJEITO'
        )
    ),
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);