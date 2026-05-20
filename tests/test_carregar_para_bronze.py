import psycopg2
import pytest

from scripts.extratores.extrair_times import (
    CONFIG_BANCO,
    criar_tabela_bronze,
    carregar_para_bronze,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def conexao():
    """Abre conexão com Supabase e fecha no final de cada teste."""
    conn = psycopg2.connect(**CONFIG_BANCO)
    yield conn
    conn.close()


@pytest.fixture
def dados_de_exemplo():
    """3 times falsos pra teste — não chama a API."""
    return [
        {
            "id": 9999001,
            "full_name": "Time Teste A",
            "abbreviation": "TTA",
            "nickname": "Testes",
            "city": "Cidade A",
            "state": "Estado A",
            "year_founded": 2020,
        },
        {
            "id": 9999002,
            "full_name": "Time Teste B",
            "abbreviation": "TTB",
            "nickname": "Testers",
            "city": "Cidade B",
            "state": "Estado B",
            "year_founded": 2021,
        },
        {
            "id": 9999003,
            "full_name": "Time Teste C",
            "abbreviation": "TTC",
            "nickname": "Testando",
            "city": "Cidade C",
            "state": "Estado C",
            "year_founded": 2022,
        },
    ]


@pytest.fixture(autouse=True)
def limpar_dados_de_teste(conexao):
    """Limpa registros de teste antes E depois de cada teste."""
    with conexao.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS bronze.times ();"
        )  # garante existência mínima
    conexao.commit()

    with conexao.cursor() as cur:
        cur.execute("DELETE FROM bronze.times WHERE id >= 9999000;")
    conexao.commit()

    yield

    with conexao.cursor() as cur:
        cur.execute("DELETE FROM bronze.times WHERE id >= 9999000;")
    conexao.commit()


# -----------------------------------------------------------------------------
# Testes
# -----------------------------------------------------------------------------
@pytest.mark.integration
def test_carrega_dados_e_retorna_quantidade(conexao, dados_de_exemplo):
    """Carga inicial: 3 times, retorna 3 linhas afetadas."""
    criar_tabela_bronze(conexao)
    n = carregar_para_bronze(conexao, dados_de_exemplo)
    assert n == 3


@pytest.mark.integration
def test_idempotencia_nao_duplica(conexao, dados_de_exemplo):
    """Rodar 2x não deve duplicar registros."""
    criar_tabela_bronze(conexao)
    carregar_para_bronze(conexao, dados_de_exemplo)
    carregar_para_bronze(conexao, dados_de_exemplo)

    with conexao.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM bronze.times WHERE id >= 9999000;")
        total = cur.fetchone()[0]

    assert total == 3, f"Esperado 3 linhas, mas tem {total} (duplicou!)"


@pytest.mark.integration
def test_upsert_atualiza_dados_alterados(conexao, dados_de_exemplo):
    """Se mudar o nome do time, o UPSERT atualiza ao invés de duplicar."""
    criar_tabela_bronze(conexao)
    carregar_para_bronze(conexao, dados_de_exemplo)

    # Altera o nome do Time Teste A
    dados_alterados = [dict(dados_de_exemplo[0])]
    dados_alterados[0]["full_name"] = "Time Teste A ATUALIZADO"
    carregar_para_bronze(conexao, dados_alterados)

    with conexao.cursor() as cur:
        cur.execute("SELECT full_name FROM bronze.times WHERE id = 9999001;")
        nome = cur.fetchone()[0]

    assert nome == "Time Teste A ATUALIZADO"


@pytest.mark.integration
def test_data_ingestao_e_preenchida(conexao, dados_de_exemplo):
    """A coluna data_ingestao não pode ficar nula (tem DEFAULT NOW())."""
    criar_tabela_bronze(conexao)
    carregar_para_bronze(conexao, dados_de_exemplo)

    with conexao.cursor() as cur:
        cur.execute(
            "SELECT data_ingestao FROM bronze.times WHERE id = 9999001;"
        )
        data = cur.fetchone()[0]

    assert data is not None


@pytest.mark.integration
def test_metadados_de_pipeline_preenchidos(conexao, dados_de_exemplo):
    """id_execucao_pipeline e fonte devem estar preenchidos."""
    criar_tabela_bronze(conexao)
    carregar_para_bronze(conexao, dados_de_exemplo)

    with conexao.cursor() as cur:
        cur.execute("""
            SELECT id_execucao_pipeline, fonte 
            FROM bronze.times 
            WHERE id = 9999001;
        """)
        run_id, fonte = cur.fetchone()

    assert run_id is not None
    assert fonte == "nba_api.stats.static.teams"