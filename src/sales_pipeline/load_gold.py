
import csv
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

GOLD_DIR = ROOT_DIR / "data" / "gold"

TABLES = {
    "sales_daily": {
        "columns": {
            "order_date": "DATE",
            "order_count": "INTEGER",
            "units_sold": "BIGINT",
            "gross_order_value": "NUMERIC(18,2)",
            "completed_order_value": "NUMERIC(18,2)",
        },
    },
    "sales_by_category": {
        "columns": {
            "category": "TEXT",
            "order_count": "INTEGER",
            "units_sold": "BIGINT",
            "gross_order_value": "NUMERIC(18,2)",
            "completed_order_value": "NUMERIC(18,2)",
        },
    },
    "sales_by_product": {
        "columns": {
            "product_id": "INTEGER",
            "product_name": "TEXT",
            "category": "TEXT",
            "order_count": "INTEGER",
            "units_sold": "BIGINT",
            "gross_order_value": "NUMERIC(18,2)",
            "completed_order_value": "NUMERIC(18,2)",
        },
    },
    "sales_by_status": {
        "columns": {
            "status": "TEXT",
            "order_count": "INTEGER",
            "units_sold": "BIGINT",
            "gross_order_value": "NUMERIC(18,2)",
        },
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
                cursor.execute("CREATE SCHEMA IF NOT EXISTS gold")

                for table_name, config in TABLES.items():
                    csv_path = GOLD_DIR / f"{table_name}.csv"
                    columns = config["columns"]

                    if not csv_path.exists():
                        raise FileNotFoundError(csv_path)

                    definitions = ", ".join(
                        f'"{name}" {sql_type}'
                        for name, sql_type in columns.items()
                    )

                    cursor.execute(
                        f'DROP TABLE IF EXISTS gold."{table_name}"'
                    )
                    cursor.execute(
                        f'CREATE TABLE gold."{table_name}" '
                        f"({definitions})"
                    )

                    column_list = ", ".join(
                        f'"{name}"' for name in columns
                    )

                    copy_sql = (
                        f'COPY gold."{table_name}" ({column_list}) '
                        "FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
                    )

                    with csv_path.open(
                        "r", encoding="utf-8", newline=""
                    ) as csv_file:
                        cursor.copy_expert(copy_sql, csv_file)

                    cursor.execute(
                        f'SELECT COUNT(*) FROM gold."{table_name}"'
                    )
                    row_count = cursor.fetchone()[0]

                    print(
                        f"gold.{table_name}: "
                        f"{row_count:,} registros carregados"
                    )

        print("\nCarga Gold concluída!")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
