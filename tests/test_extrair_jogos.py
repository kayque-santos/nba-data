from scripts.extratores.extrair_jogos import (
    extrair_jogos,
    CONFIG_BANCO,
    criar_tabela_bronze,
)
import psycopg2
import pytest


# Uma temporada já encerrada nos testes (dados estáveis, rápido).
TEMPORADA_TESTE = ["2023-24"]


def test_extrair_jogos_retorna_lista_nao_vazia():
    """Uma temporada completa tem milhares de linhas."""
    resultado = extrair_jogos(TEMPORADA_TESTE)
    assert len(resultado) > 0


def test_extrair_jogos_estrutura_do_dict():
    """Cada jogo deve ter as chaves que a carga Bronze depende."""
    resultado = extrair_jogos(TEMPORADA_TESTE)
    chaves_esperadas = {
        "GAME_ID",
        "TEAM_ID",
        "SEASON_ID",
        "TEMPORADA",
        "TEAM_ABBREVIATION",
        "TEAM_NAME",
        "GAME_DATE",
        "MATCHUP",
        "WL",
        "PTS",
    }
    assert chaves_esperadas.issubset(resultado[0].keys()), (
        f"Chaves faltando: {chaves_esperadas - set(resultado[0].keys())}"
    )


def test_extrair_jogos_chave_composta_unica():
    """(GAME_ID, TEAM_ID) único — garantia da PK da Bronze."""
    resultado = extrair_jogos(TEMPORADA_TESTE)
    chaves = [(jogo["GAME_ID"], jogo["TEAM_ID"]) for jogo in resultado]
    assert len(chaves) == len(set(chaves))


@pytest.fixture
def conexao():
    conn = psycopg2.connect(**CONFIG_BANCO)
    yield conn
    conn.close()


@pytest.mark.integration
def test_criar_tabela_bronze_executa_sem_erro(conexao):
    criar_tabela_bronze(conexao)