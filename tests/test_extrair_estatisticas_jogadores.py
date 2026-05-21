from scripts.extratores.extrair_estatisticas_jogadores import (
    extrair_estatisticas_jogadores,
    CONFIG_BANCO,
    criar_tabela_bronze,
)
import psycopg2
import pytest


# Uma temporada já encerrada nos testes (dados estáveis, rápido).
TEMPORADA_TESTE = ["2023-24"]


def test_extrair_estatisticas_retorna_lista_nao_vazia():
    """Uma temporada completa tem dezenas de milhares de linhas."""
    resultado = extrair_estatisticas_jogadores(TEMPORADA_TESTE)
    assert len(resultado) > 0


def test_extrair_estatisticas_estrutura_do_dict():
    """Cada linha deve ter as chaves que a carga Bronze depende."""
    resultado = extrair_estatisticas_jogadores(TEMPORADA_TESTE)
    chaves_esperadas = {
        "GAME_ID",
        "PLAYER_ID",
        "TEAM_ID",
        "SEASON_ID",
        "TEMPORADA",
        "PLAYER_NAME",
        "TEAM_ABBREVIATION",
        "GAME_DATE",
        "MATCHUP",
        "WL",
        "PTS",
        "AST",
        "REB",
    }
    assert chaves_esperadas.issubset(resultado[0].keys()), (
        f"Chaves faltando: {chaves_esperadas - set(resultado[0].keys())}"
    )


def test_extrair_estatisticas_chave_composta_unica():
    """(GAME_ID, PLAYER_ID) único — garantia da PK da Bronze."""
    resultado = extrair_estatisticas_jogadores(TEMPORADA_TESTE)
    chaves = [(e["GAME_ID"], e["PLAYER_ID"]) for e in resultado]
    assert len(chaves) == len(set(chaves))


@pytest.fixture
def conexao():
    conn = psycopg2.connect(**CONFIG_BANCO)
    yield conn
    conn.close()


@pytest.mark.integration
def test_criar_tabela_bronze_executa_sem_erro(conexao):
    criar_tabela_bronze(conexao)