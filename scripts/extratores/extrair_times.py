"""
Extractor: Times com IDs da balldontlie
=======================================
Necessário porque os jogos/stats vêm com IDs da balldontlie (1-30),
não com os IDs oficiais da NBA. Esta tabela permite JOIN entre as duas.

Tabela destino: bronze.times_balldontlie
Endpoint: GET /nba/v1/teams (1 request, retorna todos os 30 times)
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _client import BalldontlieClient
from _supabase import (
    iniciar_execucao,
    finalizar_execucao,
    upsert_em_lote,
)

logger = logging.getLogger(__name__)


COLUNAS = [
    'id', 'abbreviation', 'city', 'conference',
    'division', 'full_name', 'name', 'execucao_id',
]


def main(**context) -> dict:
    execucao_id = iniciar_execucao('extrair_times_balldontlie')
    logger.info(f"🏀 Iniciando extração de times balldontlie | execucao={execucao_id}")

    try:
        with BalldontlieClient() as client:
            times = list(client.paginate('/teams'))

        logger.info(f"   📦 {len(times)} times recebidos")

        linhas = [
            (
                t['id'],
                t.get('abbreviation'),
                t.get('city'),
                t.get('conference'),
                t.get('division'),
                t.get('full_name'),
                t.get('name'),
                execucao_id,
            )
            for t in times
        ]

        registros = upsert_em_lote(
            tabela='bronze.times_balldontlie',
            colunas=COLUNAS,
            linhas=linhas,
            pk_colunas=['id'],
        )

        finalizar_execucao(execucao_id, 'sucesso', registros=registros)
        logger.info(f"✅ Concluído | {registros} times balldontlie")

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