"""
Helpers Supabase compartilhados pelos extratores.

Provê:
- Conexão psycopg2 a partir de variáveis de ambiente
- UPSERT em lote (idempotente)
- Registro de execução pra auditoria
"""
import logging
import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg2
from psycopg2.extras import Json, execute_values

logger = logging.getLogger(__name__)


def conectar() -> psycopg2.extensions.connection:
    """Cria conexão Postgres a partir das envs do Supabase."""
    dsn = os.getenv('SUPABASE_DB_URL')
    if dsn:
        return psycopg2.connect(dsn)

    # Fallback: vars individuais (nomes alinhados com o .env do projeto)
    return psycopg2.connect(
        host=os.environ['SUPABASE_HOST'],
        port=int(os.environ.get('SUPABASE_PORT', 5432)),
        dbname=os.environ['SUPABASE_DB'],
        user=os.environ['SUPABASE_USER'],
        password=os.environ['SUPABASE_PASSWORD'],
    )


@contextmanager
def get_conn():
    """Context manager pra abrir/fechar conexão automaticamente."""
    conn = conectar()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def iniciar_execucao(
    extrator: str,
    parametros: Optional[dict] = None,
) -> str:
    """
    Registra início de uma execução em bronze.execucoes.
    Retorna execucao_id (UUID).
    """
    execucao_id = str(uuid.uuid4())
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bronze.execucoes (execucao_id, extrator, parametros, status)
            VALUES (%s, %s, %s, 'em_execucao')
            """,
            (execucao_id, extrator, Json(parametros) if parametros else None),
        )
    logger.info(f"📝 Execução registrada: {execucao_id}")
    return execucao_id


def finalizar_execucao(
    execucao_id: str,
    status: str,
    registros: Optional[int] = None,
    mensagem_erro: Optional[str] = None,
):
    """Atualiza execução com status final."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE bronze.execucoes
               SET fim_em = NOW(),
                   status = %s,
                   registros = %s,
                   mensagem_erro = %s
             WHERE execucao_id = %s
            """,
            (status, registros, mensagem_erro, execucao_id),
        )


def upsert_em_lote(
    tabela: str,
    colunas: list[str],
    linhas: list[tuple],
    pk_colunas: list[str],
    batch_size: int = 500,
) -> int:
    """
    UPSERT em lote usando ON CONFLICT.

    Args:
        tabela: nome qualificado, ex 'bronze.jogos'
        colunas: ['id', 'date', 'season', ...]
        linhas: lista de tuplas alinhadas com colunas
        pk_colunas: colunas que definem conflito, ex ['id']
        batch_size: registros por batch

    Returns: número de linhas afetadas.
    """
    if not linhas:
        logger.info(f"   ⚪ Nada pra upsertar em {tabela}")
        return 0

    cols_sql = ', '.join(colunas)
    pk_sql = ', '.join(pk_colunas)

    # Atualiza todas as colunas que NÃO são PK
    update_cols = [c for c in colunas if c not in pk_colunas]
    set_sql = ', '.join(f"{c} = EXCLUDED.{c}" for c in update_cols)

    if update_cols:
        sql = f"""
            INSERT INTO {tabela} ({cols_sql})
            VALUES %s
            ON CONFLICT ({pk_sql}) DO UPDATE SET {set_sql}
        """
    else:
        # Só PKs - se conflitar, ignora
        sql = f"""
            INSERT INTO {tabela} ({cols_sql})
            VALUES %s
            ON CONFLICT ({pk_sql}) DO NOTHING
        """

    total = 0
    with get_conn() as conn, conn.cursor() as cur:
        for i in range(0, len(linhas), batch_size):
            batch = linhas[i:i + batch_size]
            execute_values(cur, sql, batch, page_size=batch_size)
            total += len(batch)

    logger.info(f"   💾 {total} linhas upsertadas em {tabela}")
    return total