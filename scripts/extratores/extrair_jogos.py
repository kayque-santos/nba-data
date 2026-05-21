"""
Extractor: Jogos
================
Carrega jogos (calendário + placares) via balldontlie.io.

Tabela destino: bronze.jogos
Endpoint: GET /nba/v1/games

Modos:
  - carga_inicial(temporadas=[2023, 2024, 2025]) → carrega temporadas inteiras
  - incremental_diario(data='YYYY-MM-DD') → carrega só jogos de uma data

Rate limit (free):
  1 temporada NBA ≈ 1230 jogos = 13 páginas = ~3 min
  3 temporadas históricas ≈ 9 min
  1 data específica ≈ 1 página = 13s
"""
import logging
import sys
from datetime import date, datetime, timedelta
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
    'id', 'date', 'datetime', 'season', 'status', 'period', 'time',
    'postseason', 'home_team_id', 'home_team_score',
    'visitor_team_id', 'visitor_team_score', 'execucao_id',
]


def buscar_jogos(
    temporadas: Optional[list[int]] = None,
    datas: Optional[list[str]] = None,
) -> list[dict]:
    """
    Args:
        temporadas: lista de anos de início, ex [2023, 2024]
        datas: lista de datas 'YYYY-MM-DD' (alternativa, mais incremental)
    """
    params = {}
    if temporadas:
        params['seasons[]'] = temporadas
    if datas:
        params['dates[]'] = datas

    with BalldontlieClient() as client:
        return list(client.paginate('/games', params=params))


def normalizar(jogos: list[dict], execucao_id: str) -> list[tuple]:
    linhas = []
    for j in jogos:
        home = j.get('home_team') or {}
        visitor = j.get('visitor_team') or {}
        linhas.append((
            j['id'],
            j.get('date'),
            j.get('datetime'),
            j.get('season'),
            j.get('status'),
            j.get('period'),
            j.get('time'),
            j.get('postseason', False),
            home.get('id'),
            j.get('home_team_score'),
            visitor.get('id'),
            j.get('visitor_team_score'),
            execucao_id,
        ))
    return linhas


def main(
    temporadas: Optional[list[int]] = None,
    datas: Optional[list[str]] = None,
    **context,
) -> dict:
    """
    Modo carga inicial:
      main(temporadas=[2023, 2024, 2025])

    Modo incremental diário (Airflow):
      main(datas=['2026-05-20'])

    Se nenhum dos dois for passado, faz incremental de "ontem".
    """
    if not temporadas and not datas:
        ontem = (date.today() - timedelta(days=1)).isoformat()
        datas = [ontem]
        logger.info(f"   ℹ️  Modo padrão: incremental de {ontem}")

    parametros = {'temporadas': temporadas, 'datas': datas}
    execucao_id = iniciar_execucao('extrair_jogos', parametros=parametros)
    logger.info(f"🏀 Iniciando extração de jogos | execucao={execucao_id}")
    logger.info(f"   Parâmetros: {parametros}")

    try:
        jogos = buscar_jogos(temporadas=temporadas, datas=datas)
        logger.info(f"   📦 {len(jogos)} jogos recebidos")

        if not jogos:
            logger.info("   ⚪ Nenhum jogo no período")
            finalizar_execucao(execucao_id, 'sucesso', registros=0)
            return {'execucao_id': execucao_id, 'registros': 0}

        linhas = normalizar(jogos, execucao_id)
        registros = upsert_em_lote(
            tabela='bronze.jogos',
            colunas=COLUNAS,
            linhas=linhas,
            pk_colunas=['id'],
        )

        finalizar_execucao(execucao_id, 'sucesso', registros=registros)
        logger.info(f"✅ Concluído | {registros} jogos")

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
    # Exemplo manual: carga inicial das 3 temporadas
    # main(temporadas=[2023, 2024, 2025])
    main()