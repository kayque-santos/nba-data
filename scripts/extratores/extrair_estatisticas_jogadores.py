"""
Extractor: Estatísticas de Jogadores por Jogo (box score)
=========================================================
Carrega stats individuais via balldontlie.io.

Tabela destino: bronze.estatisticas_jogadores
Endpoint: GET /nba/v1/stats

Modos:
  - main(temporadas=[2023, 2024, 2025]) → carga inicial (DEMORADO)
  - main(datas=['2026-05-20'])           → incremental por data
  - main(game_ids=[...])                  → reextrair jogos específicos

Rate limit (free):
  1 temporada ≈ 25000 stats = 250 páginas = ~55 min
  ⚠️ Carga inicial de 3 temporadas pode levar ~3 horas
  Recomendado rodar à noite. Idempotente (pode retomar).

  Incremental diário ≈ 1-3 páginas = ~30s. Tranquilo.
"""
import logging
import sys
from datetime import date, timedelta
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
    'id', 'game_id', 'player_id', 'team_id',
    'min', 'fgm', 'fga', 'fg_pct',
    'fg3m', 'fg3a', 'fg3_pct',
    'ftm', 'fta', 'ft_pct',
    'oreb', 'dreb', 'reb', 'ast', 'stl', 'blk',
    'turnover', 'pf', 'pts',
    'execucao_id',
]


def buscar_stats(
    temporadas: Optional[list[int]] = None,
    datas: Optional[list[str]] = None,
    game_ids: Optional[list[int]] = None,
    player_ids: Optional[list[int]] = None,
) -> list[dict]:
    params = {}
    if temporadas:
        params['seasons[]'] = temporadas
    if datas:
        params['dates[]'] = datas
    if game_ids:
        params['game_ids[]'] = game_ids
    if player_ids:
        params['player_ids[]'] = player_ids

    with BalldontlieClient() as client:
        return list(client.paginate('/stats', params=params))


def _to_int(v):
    if v is None or v == '':
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _to_float(v):
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def normalizar(stats: list[dict], execucao_id: str) -> list[tuple]:
    linhas = []
    for s in stats:
        game = s.get('game') or {}
        player = s.get('player') or {}
        team = s.get('team') or {}
        linhas.append((
            s['id'],
            game.get('id'),
            player.get('id'),
            team.get('id'),
            s.get('min'),
            _to_int(s.get('fgm')),
            _to_int(s.get('fga')),
            _to_float(s.get('fg_pct')),
            _to_int(s.get('fg3m')),
            _to_int(s.get('fg3a')),
            _to_float(s.get('fg3_pct')),
            _to_int(s.get('ftm')),
            _to_int(s.get('fta')),
            _to_float(s.get('ft_pct')),
            _to_int(s.get('oreb')),
            _to_int(s.get('dreb')),
            _to_int(s.get('reb')),
            _to_int(s.get('ast')),
            _to_int(s.get('stl')),
            _to_int(s.get('blk')),
            _to_int(s.get('turnover')),
            _to_int(s.get('pf')),
            _to_int(s.get('pts')),
            execucao_id,
        ))
    return linhas


def main(
    temporadas: Optional[list[int]] = None,
    datas: Optional[list[str]] = None,
    game_ids: Optional[list[int]] = None,
    **context,
) -> dict:
    if not any([temporadas, datas, game_ids]):
        ontem = (date.today() - timedelta(days=1)).isoformat()
        datas = [ontem]
        logger.info(f"   ℹ️  Modo padrão: incremental de {ontem}")

    parametros = {'temporadas': temporadas, 'datas': datas, 'game_ids': game_ids}
    execucao_id = iniciar_execucao('extrair_estatisticas', parametros=parametros)
    logger.info(f"🏀 Iniciando extração de stats | execucao={execucao_id}")
    logger.info(f"   Parâmetros: {parametros}")

    try:
        stats = buscar_stats(
            temporadas=temporadas,
            datas=datas,
            game_ids=game_ids,
        )
        logger.info(f"   📦 {len(stats)} stats recebidos")

        if not stats:
            finalizar_execucao(execucao_id, 'sucesso', registros=0)
            return {'execucao_id': execucao_id, 'registros': 0}

        linhas = normalizar(stats, execucao_id)
        registros = upsert_em_lote(
            tabela='bronze.estatisticas_jogadores',
            colunas=COLUNAS,
            linhas=linhas,
            pk_colunas=['id'],
        )

        finalizar_execucao(execucao_id, 'sucesso', registros=registros)
        logger.info(f"✅ Concluído | {registros} stats")

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