import os
from decimal import Decimal
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def main() -> None:
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433"),
        dbname=os.getenv("DB_NAME", "sales_dw"),
        user=os.getenv("DB_USER", "sales_user"),
        password=os.getenv("DB_PASSWORD"),
    )

    errors = []

    try:
        with connection.cursor() as cursor:
            checks = [
                (
                    "Pedidos sem cliente correspondente",
                    """
                    SELECT COUNT(*)
                    FROM silver.orders o
                    LEFT JOIN silver.customers c
                        ON c.customer_id = o.customer_id
                    WHERE c.customer_id IS NULL
                    """,
                ),
                (
                    "Pedidos sem produto correspondente",
                    """
                    SELECT COUNT(*)
                    FROM silver.orders o
                    LEFT JOIN silver.products p
                        ON p.product_id = o.product_id
                    WHERE p.product_id IS NULL
                    """,
                ),
                (
                    "Chaves duplicadas de clientes",
                    """
                    SELECT COUNT(*)
                    FROM (
                        SELECT customer_id
                        FROM silver.customers
                        GROUP BY customer_id
                        HAVING COUNT(*) > 1
                    ) duplicated
                    """,
                ),
                (
                    "Chaves duplicadas de produtos",
                    """
                    SELECT COUNT(*)
                    FROM (
                        SELECT product_id
                        FROM silver.products
                        GROUP BY product_id
                        HAVING COUNT(*) > 1
                    ) duplicated
                    """,
                ),
                (
                    "Chaves duplicadas de pedidos",
                    """
                    SELECT COUNT(*)
                    FROM (
                        SELECT order_id
                        FROM silver.orders
                        GROUP BY order_id
                        HAVING COUNT(*) > 1
                    ) duplicated
                    """,
                ),
            ]

            for description, query in checks:
                cursor.execute(query)
                count = cursor.fetchone()[0]

                if count:
                    errors.append(f"{description}: {count} inconsistência(s)")
                    print(f"FALHOU: {description}: {count}")
                else:
                    print(f"OK: {description}")

            cursor.execute("""
                SELECT
                    (SELECT COALESCE(SUM(order_amount), 0)
                     FROM silver.orders),
                    (SELECT COALESCE(SUM(gross_order_value), 0)
                     FROM gold.sales_daily_sql),
                    (SELECT COALESCE(SUM(gross_order_value), 0)
                     FROM gold.sales_by_status_sql),
                    (SELECT COALESCE(SUM(
                        CASE WHEN status = 'completed'
                             THEN order_amount ELSE 0 END
                     ), 0)
                     FROM silver.orders),
                    (SELECT COALESCE(SUM(completed_order_value), 0)
                     FROM gold.sales_daily_sql)
            """)

            (
                silver_gross,
                gold_daily_gross,
                gold_status_gross,
                silver_completed,
                gold_daily_completed,
            ) = cursor.fetchone()

            monetary_checks = [
                ("Vendas brutas: Silver x Gold diária",
                 silver_gross, gold_daily_gross),
                ("Vendas brutas: Silver x Gold por status",
                 silver_gross, gold_status_gross),
                ("Vendas concluídas: Silver x Gold diária",
                 silver_completed, gold_daily_completed),
            ]

            for description, source, aggregate in monetary_checks:
                source = Decimal(str(source)).quantize(Decimal("0.01"))
                aggregate = Decimal(str(aggregate)).quantize(Decimal("0.01"))

                if source != aggregate:
                    errors.append(
                        f"{description}: origem={source}, agregado={aggregate}"
                    )
                    print(
                        f"FALHOU: {description}: "
                        f"origem={source}, agregado={aggregate}"
                    )
                else:
                    print(f"OK: {description}: R$ {source:,.2f}")

    finally:
        connection.close()

    if errors:
        raise SystemExit(
            f"\nValidação da Gold reprovada: {len(errors)} inconsistência(s)."
        )

    print("\nValidação da Gold concluída sem inconsistências!")


if __name__ == "__main__":
    main()
