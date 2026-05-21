from scripts.extratores.extrair_jogadores import (
    extrair_jogadores,
    CONFIG_BANCO,
    criar_tabela_bronze,
)
import psycopg2
import pytest


def test_extrair_jogadores_retorna_lista_nao_vazia():
    """Deve trazer milhares de jogadores históricos."""
    resultado = extrair_jogadores()
    assert len(resultado) > 0


def test_extrair_jogadores_estrutura_do_dict():
    """Cada jogador deve ter as chaves que a carga Bronze depende."""
    resultado = extrair_jogadores()
    chaves_esperadas = {
        "id",
        "full_name",
        "first_name",
        "last_name",
        "is_active",
    }
    assert chaves_esperadas.issubset(resultado[0].keys()), (
        f"Chaves faltando: {chaves_esperadas - set(resultado[0].keys())}"
    )


def test_extrair_jogadores_ids_unicos():
    """IDs únicos — garantia da PK da Bronze."""
    resultado = extrair_jogadores()
    ids = [jogador["id"] for jogador in resultado]
    assert len(ids) == len(set(ids))


@pytest.fixture
def conexao():
    conn = psycopg2.connect(**CONFIG_BANCO)
    yield conn
    conn.close()


@pytest.mark.integration
def test_criar_tabela_bronze_executa_sem_erro(conexao):
    criar_tabela_bronze(conexao)