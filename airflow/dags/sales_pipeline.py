
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_DIR = "/opt/airflow/project"

default_args = {
    "owner": "data-engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="sales_data_pipeline",
    description="Pipeline Raw, Silver e Gold SQL com testes de qualidade",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["sales", "data-engineering", "quality", "sql"],
) as dag:

    load_raw = BashOperator(
        task_id="load_raw",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m src.sales_pipeline.load_raw"
        ),
    )

    validate_raw = BashOperator(
        task_id="validate_raw",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m src.quality.validate_raw"
        ),
    )

    prepare_silver = BashOperator(
        task_id="prepare_silver",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m src.transform.prepare_silver"
        ),
    )

    test_silver_quality = BashOperator(
        task_id="test_silver_quality",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m pytest -v tests/"
        ),
    )

    load_silver = BashOperator(
        task_id="load_silver",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m src.sales_pipeline.load_silver"
        ),
    )

    build_gold_sql = BashOperator(
        task_id="build_gold_sql",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m src.analytics.build_gold_sql"
        ),
    )

    validate_gold = BashOperator(
        task_id="validate_gold",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m src.quality.validate_gold"
        ),
    )

    (
        load_raw
        >> validate_raw
        >> prepare_silver
        >> test_silver_quality
        >> load_silver
        >> build_gold_sql
        >> validate_gold
    )
