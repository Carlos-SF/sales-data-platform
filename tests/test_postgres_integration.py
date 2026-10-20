import os

import psycopg2
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def db_connection():
    """Abre uma conexão real com o PostgreSQL do projeto."""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433"),
        dbname=os.getenv("DB_NAME", "sales_dw"),
        user=os.getenv("DB_USER", "sales_user"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5,
    )

    try:
        yield conn
    finally:
        conn.close()


def test_postgres_contains_raw_silver_and_gold(db_connection):
    """Confere se as tabelas principais existem no banco."""
    expected_tables = [
        ("raw", "customers"),
        ("raw", "orders"),
        ("raw", "products"),
        ("silver", "customers"),
        ("silver", "orders"),
        ("silver", "products"),
        ("gold", "sales_daily_sql"),
        ("gold", "sales_by_category_sql"),
        ("gold", "sales_by_product_sql"),
        ("gold", "sales_by_status_sql"),
    ]

    with db_connection.cursor() as cursor:
        for schema, table in expected_tables:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = %s
                      AND table_name = %s
                );
                """,
                (schema, table),
            )

            assert cursor.fetchone()[0], (
                f"Tabela ausente: {schema}.{table}"
            )


@pytest.mark.parametrize(
    ("table", "expected_count"),
    [
        ("customers", 10_000),
        ("products", 500),
        ("orders", 100_000),
    ],
)
def test_silver_row_counts(db_connection, table, expected_count):
    """Confere os volumes esperados nas tabelas Silver."""
    with db_connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM silver.{table};")
        actual_count = cursor.fetchone()[0]

    assert actual_count == expected_count


@pytest.mark.parametrize(
    ("table", "expected_count"),
    [
        ("sales_daily_sql", 1019),
        ("sales_by_category_sql", 8),
        ("sales_by_product_sql", 500),
        ("sales_by_status_sql", 4),
    ],
)
def test_gold_row_counts(db_connection, table, expected_count):
    """Confere os volumes esperados nas tabelas analíticas Gold."""
    with db_connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM gold.{table};")
        actual_count = cursor.fetchone()[0]

    assert actual_count == expected_count


def test_gold_financial_totals(db_connection):
    """Confere os valores financeiros persistidos na Gold."""
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                SUM(gross_order_value),
                SUM(completed_order_value)
            FROM gold.sales_daily_sql;
            """
        )
        gross_total, completed_total = cursor.fetchone()

    assert float(gross_total) == pytest.approx(
        811_884_574.08, abs=0.01
    )
    assert float(completed_total) == pytest.approx(
        586_385_508.02, abs=0.01
    )
