from io import StringIO
import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"

load_dotenv(ROOT_DIR / ".env")

TABLES = {
    "customers": [
        "customer_id",
        "customer_name",
        "city",
        "state",
    ],
    "orders": [
        "order_id",
        "customer_id",
        "product_id",
        "order_date",
        "quantity",
        "unit_price",
        "status",
    ],
    "products": [
        "product_id",
        "product_name",
        "category",
    ],
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
                # Garante que o schema e as tabelas existam.
                schema_sql = (
                    ROOT_DIR / "sql" / "01_raw_schema.sql"
                ).read_text(encoding="utf-8")
                cursor.execute(schema_sql)

                dataframes = {}

                # Validar os arquivos antes de substituir os dados.
                for table_name, expected_columns in TABLES.items():
                    csv_path = RAW_DIR / f"{table_name}.csv"

                    if not csv_path.exists():
                        raise FileNotFoundError(csv_path)

                    df = pd.read_csv(csv_path)

                    if list(df.columns) != expected_columns:
                        raise ValueError(
                            f"Colunas inesperadas em {csv_path.name}. "
                            f"Esperadas: {expected_columns}; "
                            f"encontradas: {list(df.columns)}"
                        )

                    dataframes[table_name] = df

                # Carga completa e transacional somente da camada Raw.
                cursor.execute(
                    "TRUNCATE TABLE "
                    "raw.orders, raw.customers, raw.products"
                )

                for table_name, df in dataframes.items():
                    df = df.copy()
                    df["source_file"] = f"{table_name}.csv"

                    buffer = StringIO()
                    df.to_csv(
                        buffer,
                        index=False,
                        header=False,
                        na_rep="",
                    )
                    buffer.seek(0)

                    columns = TABLES[table_name] + ["source_file"]
                    column_list = ", ".join(
                        f'"{column}"' for column in columns
                    )

                    cursor.copy_expert(
                        f"COPY raw.{table_name} ({column_list}) "
                        "FROM STDIN WITH (FORMAT CSV)",
                        buffer,
                    )

                    print(
                        f"raw.{table_name}: "
                        f"{len(df):,} registros carregados"
                    )

        print("\nCarga Raw concluída!")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
