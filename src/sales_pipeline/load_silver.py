import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
SILVER_DIR = ROOT_DIR / "data" / "silver"

load_dotenv(ROOT_DIR / ".env")


TABLES = {
    "customers": {
        "file": "customers.csv",
        "columns": ["customer_id", "customer_name", "city", "state"],
        "types": """
            customer_id BIGINT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            city TEXT,
            state CHAR(2)
        """,
    },
    "products": {
        "file": "products.csv",
        "columns": ["product_id", "product_name", "category"],
        "types": """
            product_id BIGINT PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT
        """,
    },
    "orders": {
        "file": "orders.csv",
        "columns": [
            "order_id",
            "customer_id",
            "product_id",
            "order_date",
            "quantity",
            "unit_price",
            "status",
            "order_amount",
        ],
        "types": """
            order_id BIGINT PRIMARY KEY,
            customer_id BIGINT NOT NULL,
            product_id BIGINT NOT NULL,
            order_date DATE NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price > 0),
            status VARCHAR(30) NOT NULL,
            order_amount NUMERIC(14,2) NOT NULL
        """,
    },
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
                cursor.execute("CREATE SCHEMA IF NOT EXISTS silver")

                for table_name, config in TABLES.items():
                    path = SILVER_DIR / config["file"]
                    if not path.exists():
                        raise FileNotFoundError(path)

                    dataframe = pd.read_csv(path)

                    missing = set(config["columns"]) - set(dataframe.columns)
                    if missing:
                        raise ValueError(
                            f"{path.name} não contém as colunas: "
                            f"{sorted(missing)}"
                        )

                    dataframe = dataframe[config["columns"]]

                    cursor.execute(
                        f'DROP TABLE IF EXISTS silver."{table_name}"'
                    )
                    cursor.execute(
                        f'CREATE TABLE silver."{table_name}" '
                        f'({config["types"]})'
                    )

                    columns_sql = ", ".join(
                        f'"{column}"' for column in config["columns"]
                    )
                    copy_sql = (
                        f'COPY silver."{table_name}" ({columns_sql}) '
                        "FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
                    )

                    from io import StringIO

                    buffer = StringIO()
                    dataframe.to_csv(buffer, index=False)
                    buffer.seek(0)
                    cursor.copy_expert(copy_sql, buffer)

                    cursor.execute(
                        f'SELECT COUNT(*) FROM silver."{table_name}"'
                    )
                    count = cursor.fetchone()[0]
                    print(f"silver.{table_name}: {count:,} registros")

        print("Carga da camada Silver concluída!")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
