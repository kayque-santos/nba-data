from scripts.extratores.extrair_times import extrair_times, CONFIG_BANCO, criar_tabela_bronze
import psycopg2
import pytest




def test_extrair_times_retorna_lista():
    """A função deve retornar uma lista."""
    resultado = extrair_times()
    assert isinstance(resultado, list)


def test_extrair_times_retorna_30_times():
    """A NBA tem 30 times — a extração deve trazer todos."""
    resultado = extrair_times()
    assert len(resultado) == 30


def test_extrair_times_estrutura_do_dict():
    """Cada time deve ter as chaves esperadas vindas da API."""
    resultado = extrair_times()
    primeiro_time = resultado[0]

    chaves_esperadas = {
        "id",
        "full_name",
        "abbreviation",
        "nickname",
        "city",
        "state",
        "year_founded",
    }

    assert chaves_esperadas.issubset(primeiro_time.keys()), (
        f"Chaves faltando: {chaves_esperadas - set(primeiro_time.keys())}"
    )


def test_extrair_times_id_e_inteiro():
    """O ID do time deve ser inteiro."""
    resultado = extrair_times()
    assert isinstance(resultado[0]["id"], int)


def test_extrair_times_nao_tem_ids_duplicados():
    """Não pode ter times com mesmo ID (garantia de unicidade)."""
    resultado = extrair_times()
    ids = [time["id"] for time in resultado]
    assert len(ids) == len(set(ids)), "Existem IDs duplicados!"


@pytest.fixture
def conexao():
    """Abre uma conexão com o banco e fecha no final do teste."""
    conn = psycopg2.connect(**CONFIG_BANCO)
    yield conn
    conn.close()


@pytest.mark.integration
def test_criar_tabela_bronze_executa_sem_erro(conexao):
    """A criação da tabela deve rodar sem lançar exceção."""
    criar_tabela_bronze(conexao)