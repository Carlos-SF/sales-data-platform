
import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
SILVER_DIR = ROOT_DIR / "data" / "silver"

load_dotenv(ROOT_DIR / ".env")


def read_raw_tables(connection):
    """Lê as tabelas Raw diretamente do PostgreSQL."""
    customers = pd.read_sql_query(
        """
        SELECT customer_id, customer_name, city, state
        FROM raw.customers
        """,
        connection,
    )

    products = pd.read_sql_query(
        """
        SELECT product_id, product_name, category
        FROM raw.products
        """,
        connection,
    )

    orders = pd.read_sql_query(
        """
        SELECT order_id, customer_id, product_id,
               order_date, quantity, unit_price, status
        FROM raw.orders
        """,
        connection,
    )

    return customers, products, orders


def main() -> None:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433"),
        dbname=os.getenv("DB_NAME", "sales_dw"),
        user=os.getenv("DB_USER", "sales_user"),
        password=os.getenv("DB_PASSWORD"),
    )

    try:
        customers, products, orders = read_raw_tables(connection)
    finally:
        connection.close()

    if customers.empty or products.empty or orders.empty:
        raise ValueError(
            "Uma ou mais tabelas Raw estão vazias. "
            "Verifique a carga antes de gerar a Silver."
        )

    # Padronizar textos
    for column in ["customer_name", "city", "state"]:
        customers[column] = (
            customers[column].astype("string").str.strip()
        )

    for column in ["product_name", "category"]:
        products[column] = (
            products[column].astype("string").str.strip()
        )

    orders["status"] = (
        orders["status"].astype("string").str.strip().str.lower()
    )

    # Converter os tipos dos pedidos
    orders["order_date"] = pd.to_datetime(
        orders["order_date"], errors="coerce"
    )
    orders["quantity"] = pd.to_numeric(
        orders["quantity"], errors="coerce"
    )
    orders["unit_price"] = pd.to_numeric(
        orders["unit_price"], errors="coerce"
    )

    # Validar os dados convertidos
    if orders[
        ["order_date", "quantity", "unit_price"]
    ].isna().any().any():
        raise ValueError(
            "Existem datas, quantidades ou preços inválidos."
        )

    if (orders["quantity"] <= 0).any():
        raise ValueError(
            "Existem quantidades menores ou iguais a zero."
        )

    if (orders["unit_price"] <= 0).any():
        raise ValueError(
            "Existem preços menores ou iguais a zero."
        )

    # Criar métrica de valor bruto
    orders["order_amount"] = (
        orders["quantity"] * orders["unit_price"]
    ).round(2)

    orders["order_date"] = (
        orders["order_date"].dt.strftime("%Y-%m-%d")
    )

    # Manter os CSVs Silver usados pelas etapas seguintes
    customers.to_csv(SILVER_DIR / "customers.csv", index=False)
    products.to_csv(SILVER_DIR / "products.csv", index=False)
    orders.to_csv(SILVER_DIR / "orders.csv", index=False)

    print("Transformação Silver concluída!")
    print(f"Clientes: {len(customers):,}")
    print(f"Produtos: {len(products):,}")
    print(f"Pedidos: {len(orders):,}")
    print(
        f"Valor bruto total: "
        f"R$ {orders['order_amount'].sum():,.2f}"
    )
    print(f"Arquivos salvos em: {SILVER_DIR}")


if __name__ == "__main__":
    main()
