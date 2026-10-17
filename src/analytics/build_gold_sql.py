import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


QUERIES = {
    "sales_daily": """
        SELECT
            o.order_date,
            COUNT(DISTINCT o.order_id)::INTEGER AS order_count,
            SUM(o.quantity)::BIGINT AS units_sold,
            ROUND(SUM(o.order_amount), 2) AS gross_order_value,
            ROUND(SUM(
                CASE WHEN o.status = 'completed'
                     THEN o.order_amount ELSE 0 END
            ), 2) AS completed_order_value
        FROM silver.orders o
        GROUP BY o.order_date
        ORDER BY o.order_date
    """,
    "sales_by_category": """
        SELECT
            p.category,
            COUNT(DISTINCT o.order_id)::INTEGER AS order_count,
            SUM(o.quantity)::BIGINT AS units_sold,
            ROUND(SUM(o.order_amount), 2) AS gross_order_value,
            ROUND(SUM(
                CASE WHEN o.status = 'completed'
                     THEN o.order_amount ELSE 0 END
            ), 2) AS completed_order_value
        FROM silver.orders o
        JOIN silver.products p ON p.product_id = o.product_id
        GROUP BY p.category
        ORDER BY gross_order_value DESC
    """,
    "sales_by_product": """
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            COUNT(DISTINCT o.order_id)::INTEGER AS order_count,
            SUM(o.quantity)::BIGINT AS units_sold,
            ROUND(SUM(o.order_amount), 2) AS gross_order_value,
            ROUND(SUM(
                CASE WHEN o.status = 'completed'
                     THEN o.order_amount ELSE 0 END
            ), 2) AS completed_order_value
        FROM silver.orders o
        JOIN silver.products p ON p.product_id = o.product_id
        GROUP BY p.product_id, p.product_name, p.category
        ORDER BY gross_order_value DESC
    """,
    "sales_by_status": """
        SELECT
            status,
            COUNT(DISTINCT order_id)::INTEGER AS order_count,
            SUM(quantity)::BIGINT AS units_sold,
            ROUND(SUM(order_amount), 2) AS gross_order_value
        FROM silver.orders
        GROUP BY status
        ORDER BY gross_order_value DESC
    """,
}


def main() -> None:
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433"),
        dbname=os.getenv("DB_NAME", "sales_dw"),
        user=os.getenv("DB_USER", "sales_user"),
        password=os.getenv("DB_PASSWORD"),
    )

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE SCHEMA IF NOT EXISTS gold")

                for table_name, query in QUERIES.items():
                    cursor.execute(
                        f'DROP TABLE IF EXISTS gold."{table_name}_sql"'
                    )
                    cursor.execute(
                        f'CREATE TABLE gold."{table_name}_sql" AS {query}'
                    )
                    cursor.execute(
                        f'SELECT COUNT(*) FROM gold."{table_name}_sql"'
                    )
                    count = cursor.fetchone()[0]
                    print(f"gold.{table_name}_sql: {count:,} registros")

                cursor.execute("""
                    SELECT
                        ROUND(SUM(gross_order_value), 2),
                        ROUND(SUM(completed_order_value), 2)
                    FROM gold.sales_daily_sql
                """)
                gross, completed = cursor.fetchone()
                print(f"Valor bruto Gold: R$ {gross:,.2f}")
                print(f"Valor concluído Gold: R$ {completed:,.2f}")

        print("Construção da Gold por SQL concluída!")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
