-- Migração 002: Tabelas e índices para importação de comprovantes Pix em lote
-- Reversível / Não destrutiva

BEGIN;

CREATE TABLE IF NOT EXISTS lotes_importacao (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'PROCESSANDO',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lotes_usuario_id ON lotes_importacao(usuario_id);
CREATE INDEX IF NOT EXISTS idx_lotes_status ON lotes_importacao(status);
CREATE INDEX IF NOT EXISTS idx_lotes_created_at ON lotes_importacao(created_at);

CREATE TABLE IF NOT EXISTS itens_importacao (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER NOT NULL REFERENCES lotes_importacao(id) ON DELETE CASCADE,
    nome_arquivo VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    hash_sha256 VARCHAR(64),
    
    banco VARCHAR(100),
    pagador VARCHAR(255),
    valor NUMERIC(12, 2),
    data_hora VARCHAR(100),
    id_transacao VARCHAR(255),
    
    paciente_id INTEGER REFERENCES pacientes(id) ON DELETE SET NULL,
    sessoes_pagas INTEGER NOT NULL DEFAULT 1,
    valor_sessao_sugerido NUMERIC(12, 2),
    
    dados_extraidos JSONB,
    
    status VARCHAR(50) NOT NULL DEFAULT 'PROCESSANDO',
    etapa_erro VARCHAR(50),
    mensagem_erro TEXT,
    
    pagamento_id INTEGER UNIQUE REFERENCES pagamentos(id) ON DELETE SET NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_itens_lote_id ON itens_importacao(lote_id);
CREATE INDEX IF NOT EXISTS idx_itens_status ON itens_importacao(status);
CREATE INDEX IF NOT EXISTS idx_itens_paciente_id ON itens_importacao(paciente_id);
CREATE INDEX IF NOT EXISTS idx_itens_created_at ON itens_importacao(created_at);

COMMIT;

