-- Execute after backup. PostgreSQL migration for existing installations.
ALTER TABLE pacientes
    ALTER COLUMN valor_sessao TYPE NUMERIC(12, 2)
    USING ROUND(valor_sessao::numeric, 2);

ALTER TABLE pagamentos
    ALTER COLUMN valor TYPE NUMERIC(12, 2)
    USING ROUND(valor::numeric, 2);

ALTER TABLE pagamentos
    ADD COLUMN IF NOT EXISTS data_hora_nova TIMESTAMPTZ;

UPDATE pagamentos
SET data_hora_nova = CASE
    WHEN data_hora ~ '^[0-9]{2}/[0-9]{2}/[0-9]{4} [0-9]{2}:[0-9]{2}$'
        THEN to_timestamp(data_hora, 'DD/MM/YYYY HH24:MI')
             AT TIME ZONE 'America/Sao_Paulo'
    WHEN data_hora ~ '^[0-9]{2}/[0-9]{2}/[0-9]{4}$'
        THEN to_timestamp(data_hora, 'DD/MM/YYYY')
             AT TIME ZONE 'America/Sao_Paulo'
    WHEN data_hora ~ 'Z$|[+-][0-9]{2}:[0-9]{2}$'
        THEN data_hora::timestamptz
    WHEN data_hora ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}([T ][0-9]{2}:[0-9]{2}(:[0-9]{2})?)?$'
        THEN to_timestamp(
                 replace(data_hora, 'T', ' '),
                 CASE
                     WHEN length(replace(data_hora, 'T', ' ')) = 16
                         THEN 'YYYY-MM-DD HH24:MI'
                     ELSE 'YYYY-MM-DD HH24:MI:SS'
                 END
             ) AT TIME ZONE 'America/Sao_Paulo'
    ELSE NULL
END;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pagamentos
        WHERE data_hora IS NOT NULL
          AND data_hora_nova IS NULL
    ) THEN
        RAISE EXCEPTION 'Existem pagamentos com data_hora inválida; migração cancelada';
    END IF;
END $$;

ALTER TABLE pagamentos DROP COLUMN data_hora;
ALTER TABLE pagamentos RENAME COLUMN data_hora_nova TO data_hora;

ALTER TABLE pagamentos
    ADD COLUMN IF NOT EXISTS idempotencia_chave VARCHAR(255);

CREATE UNIQUE INDEX IF NOT EXISTS uq_pagamentos_idempotencia_chave
    ON pagamentos (idempotencia_chave)
    WHERE idempotencia_chave IS NOT NULL;
