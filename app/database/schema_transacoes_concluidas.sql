CREATE UNIQUE INDEX IF NOT EXISTS ux_transacoes_lote_concluido
ON transacoes (lote_id)
WHERE status = 'CONCLUIDA';