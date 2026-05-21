from scripts.extratores.extrair_times import (
    extrair_times,
    CONFIG_BANCO,
    criar_tabela_bronze,
)
import psycopg2
import pytest


def test_extrair_times_retorna_lista_nao_vazia():
    """A NBA tem 30 times — a extração deve trazer todos."""
    resultado = extrair_times()
    assert len(resultado) == 30


def test_extrair_times_estrutura_do_dict():
    """Cada time deve ter as chaves que a carga Bronze depende."""
    resultado = extrair_times()
    chaves_esperadas = {
        "id",
        "full_name",
        "abbreviation",
        "nickname",
        "city",
        "state",
        "year_founded",
    }
    assert chaves_esperadas.issubset(resultado[0].keys()), (
        f"Chaves faltando: {chaves_esperadas - set(resultado[0].keys())}"
    )


def test_extrair_times_ids_unicos():
    """IDs únicos — garantia da PK da Bronze."""
    resultado = extrair_times()
    ids = [time["id"] for time in resultado]
    assert len(ids) == len(set(ids))


@pytest.fixture
def conexao():
    conn = psycopg2.connect(**CONFIG_BANCO)
    yield conn
    conn.close()


@pytest.mark.integration
def test_criar_tabela_bronze_executa_sem_erro(conexao):
    criar_tabela_bronze(conexao)