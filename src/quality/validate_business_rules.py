
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"


def main() -> None:
    customers = pd.read_csv(RAW_DIR / "customers.csv")
    orders = pd.read_csv(RAW_DIR / "orders.csv")
    products = pd.read_csv(RAW_DIR / "products.csv")

    checks = {
        "IDs de pedidos duplicados":
            orders["order_id"].duplicated().sum(),

        "IDs de clientes duplicados":
            customers["customer_id"].duplicated().sum(),

        "IDs de produtos duplicados":
            products["product_id"].duplicated().sum(),

        "Pedidos sem cliente":
            (~orders["customer_id"].isin(
                customers["customer_id"]
            )).sum(),

        "Pedidos sem produto":
            (~orders["product_id"].isin(
                products["product_id"]
            )).sum(),

        "Quantidades menores ou iguais a zero":
            (orders["quantity"] <= 0).sum(),

        "Preços negativos ou iguais a zero":
            (orders["unit_price"] <= 0).sum(),

        "Datas inválidas":
            pd.to_datetime(
                orders["order_date"], errors="coerce"
            ).isna().sum(),

        "Status vazios":
            orders["status"].isna().sum(),
    }

    print("\nRELATÓRIO DE REGRAS DE NEGÓCIO")
    print("=" * 45)

    failed = False

    for rule, count in checks.items():
        result = "APROVADO" if count == 0 else "REPROVADO"
        print(f"{rule}: {count} - {result}")

        if count > 0:
            failed = True

    print("=" * 45)

    if failed:
        raise SystemExit(
            "Foram encontradas violações nas regras."
        )

    print("Todas as regras foram aprovadas.")


if __name__ == "__main__":
    main()
