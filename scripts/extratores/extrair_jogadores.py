"""
Extractor: Jogadores
====================
Carrega cadastro de jogadores via balldontlie.io.

Tabela destino: bronze.jogadores
Endpoint: GET /nba/v1/players (paginado)

Atenção rate limit:
  Free tier = 5 req/min. Cada página tem 100 jogadores.
  ~5000 jogadores históricos = 50 páginas = ~10 min de execução.

Estratégia:
  - Carga inicial: extrai todos
  - Incremental: filtrar por team_id pega só os ativos (mais leve)
"""
import logging
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from _client import BalldontlieClient
from _supabase import (
    iniciar_execucao,
    finalizar_execucao,
    upsert_em_lote,
)

logger = logging.getLogger(__name__)


COLUNAS = [
    'id', 'first_name', 'last_name', 'position',
    'height', 'weight', 'jersey_number', 'college', 'country',
    'draft_year', 'draft_round', 'draft_number',
    'team_id', 'execucao_id',
]


def extrair_jogadores(
    apenas_ativos: bool = False,
    times_balldontlie_ids: Optional[list[int]] = None,
) -> list[dict]:
    """
    Args:
        apenas_ativos: se True, filtra só jogadores em times ativos
        times_balldontlie_ids: lista de team_ids da balldontlie pra filtrar
    """
    params = {}
    if apenas_ativos and times_balldontlie_ids:
        # API aceita múltiplos team_ids[] como filtro
        params['team_ids[]'] = times_balldontlie_ids

    with BalldontlieClient() as client:
        return list(client.paginate('/players', params=params))


def normalizar(jogadores: list[dict], execucao_id: str) -> list[tuple]:
    linhas = []
    for j in jogadores:
        team = j.get('team') or {}
        linhas.append((
            j['id'],
            j.get('first_name'),
            j.get('last_name'),
            j.get('position'),
            j.get('height'),
            j.get('weight'),
            j.get('jersey_number'),
            j.get('college'),
            j.get('country'),
            j.get('draft_year'),
            j.get('draft_round'),
            j.get('draft_number'),
            team.get('id') if team else None,
            execucao_id,
        ))
    return linhas


def main(apenas_ativos: bool = False, **context) -> dict:
    """
    Args:
        apenas_ativos: True pra incremental (só times ativos), False pra carga inicial
    """
    parametros = {'apenas_ativos': apenas_ativos}
    execucao_id = iniciar_execucao('extrair_jogadores', parametros=parametros)
    logger.info(
        f"🏀 Iniciando extração de jogadores "
        f"(apenas_ativos={apenas_ativos}) | execucao={execucao_id}"
    )

    try:
        # Se incremental, busca IDs dos times balldontlie pra filtrar
        times_ids = None
        if apenas_ativos:
            from _supabase import get_conn
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("SELECT id FROM bronze.times_balldontlie ORDER BY id")
                times_ids = [r[0] for r in cur.fetchall()]
            logger.info(f"   🎯 Filtrando por {len(times_ids)} times ativos")

        jogadores = extrair_jogadores(
            apenas_ativos=apenas_ativos,
            times_balldontlie_ids=times_ids,
        )
        logger.info(f"   📦 {len(jogadores)} jogadores recebidos")

        linhas = normalizar(jogadores, execucao_id)
        registros = upsert_em_lote(
            tabela='bronze.jogadores',
            colunas=COLUNAS,
            linhas=linhas,
            pk_colunas=['id'],
        )

        finalizar_execucao(execucao_id, 'sucesso', registros=registros)
        logger.info(f"✅ Concluído | {registros} jogadores")

        return {
            'execucao_id': execucao_id,
            'registros': registros,
        }

    except Exception as e:
        logger.exception(f"❌ Erro: {e}")
        finalizar_execucao(execucao_id, 'falha', mensagem_erro=str(e))
        raise


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )
    main()