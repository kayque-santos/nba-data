"""
Extractor: Times da NBA
========================

Extrai a lista de times da NBA via nba_api e carrega na camada Bronze do Supabase.

Uso:
    python scripts/extratores/extrair_times.py

Fonte:
    nba_api.stats.static.teams.get_teams()

Tabela destino:
    bronze.times
"""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

from dotenv import load_dotenv
from nba_api.stats.static import teams
import psycopg2
from psycopg2.extras import execute_values

# -----------------------------------------------------------------------------
# Configuração
# -----------------------------------------------------------------------------
load_dotenv()

# TODO 1: monta o dicionário `CONFIG_BANCO` lendo as variáveis do .env
# Dica: olha o validar_supabase.py — você já fez isso lá!
CONFIG_BANCO = {
    "host": os.getenv("SUPABASE_HOST"),
    "port": os.getenv("SUPABASE_PORT"),
    "dbname": os.getenv("SUPABASE_DB"),
    "user": os.getenv("SUPABASE_USER"),
    "password": os.getenv("SUPABASE_PASSWORD")
}

# Identificador único dessa execução (rastreabilidade)
ID_EXECUCAO_PIPELINE = str(uuid.uuid4())
FONTE = "nba_api.stats.static.teams"


# -----------------------------------------------------------------------------
# Extração
# -----------------------------------------------------------------------------
def extrair_times() -> List[Dict[str, Any]]:
    dados_times = teams.get_teams()
    return dados_times



# -----------------------------------------------------------------------------
# Carga (Bronze)
# -----------------------------------------------------------------------------
def criar_tabela_bronze(conexao) -> None:
    sql = """
    CREATE TABLE IF NOT EXISTS bronze.times (
            id                    BIGINT PRIMARY KEY,
            full_name             TEXT,
            abbreviation          TEXT,
            nickname              TEXT,
            city                  TEXT,
            state                 TEXT,
            year_founded          INTEGER,
            data_ingestao         TIMESTAMPTZ DEFAULT NOW(),
            id_execucao_pipeline  UUID,
            fonte                 TEXT
        );
        """
    with conexao.cursor() as cursor:
        cursor.execute(sql)
    conexao.commit()


def carregar_para_bronze(conexao, dados_times: List[Dict[str, Any]]) -> int:
    sql = """
        INSERT INTO bronze.times (
            id, full_name, abbreviation, nickname, city, state, year_founded,
            id_execucao_pipeline, fonte
        )
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            full_name             = EXCLUDED.full_name,
            abbreviation          = EXCLUDED.abbreviation,
            nickname              = EXCLUDED.nickname,
            city                  = EXCLUDED.city,
            state                 = EXCLUDED.state,
            year_founded          = EXCLUDED.year_founded,
            data_ingestao         = NOW(),
            id_execucao_pipeline  = EXCLUDED.id_execucao_pipeline,
            fonte                 = EXCLUDED.fonte;
    """

    valores = [
        (
            time["id"],
            time["full_name"],
            time["abbreviation"],
            time["nickname"],
            time["city"],
            time["state"],
            time["year_founded"],
            ID_EXECUCAO_PIPELINE,
            FONTE,
        )
        for time in dados_times
    ]

    with conexao.cursor() as cursor:
        execute_values(cursor, sql, valores)
        linhas_afetadas = cursor.rowcount
    conexao.commit()

    return linhas_afetadas



# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> None:
    print(f"🏀 Iniciando extração de times | execucao={ID_EXECUCAO_PIPELINE}")
    print(f"   Timestamp: {datetime.now(timezone.utc).isoformat()}")

    conexao = None
    try:
        dados_times = extrair_times()
        print(f"   Times extraídos: {len(dados_times)}")

        conexao = psycopg2.connect(**CONFIG_BANCO)
    
        criar_tabela_bronze(conexao)

        linhas_afetadas = carregar_para_bronze(conexao, dados_times)
        print(f"   Linhas afetadas: {linhas_afetadas}")

        print(f"✅ Extração concluída com sucesso")
        
    except Exception as erro:
        print(f"❌ Erro durante a extração: {erro}")
        raise

    finally:
        if conexao is not None:
            conexao.close()
            print("🔌 Conexão fechada")
            
if __name__ == "__main__":
    main()