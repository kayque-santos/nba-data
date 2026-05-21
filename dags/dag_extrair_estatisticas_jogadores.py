from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from scripts.extratores.extrair_estatisticas_jogadores import main as extrair_stats_main

default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="extrair_estatisticas_jogadores",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["nba", "bronze", "balldontlie"],
) as dag:
    PythonOperator(
        task_id="extrair_estatisticas_jogadores",
        python_callable=extrair_stats_main,
    )