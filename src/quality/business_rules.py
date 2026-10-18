
import pandas as pd


def validate_orders(orders: pd.DataFrame) -> None:
    """Valida regras essenciais dos pedidos."""

    required_columns = [
        "quantity",
        "unit_price",
        "order_date",
    ]

    missing = set(required_columns) - set(orders.columns)
    if missing:
        raise ValueError(f"Colunas ausentes: {sorted(missing)}")

    quantity = pd.to_numeric(orders["quantity"], errors="coerce")
    price = pd.to_numeric(orders["unit_price"], errors="coerce")
    dates = pd.to_datetime(
    orders["order_date"],
    format="%Y-%m-%d",
    errors="coerce",
    )

    if quantity.isna().any():
        raise ValueError("Quantidade inválida ou ausente.")

    if (quantity <= 0).any():
        raise ValueError("Quantidade deve ser maior que zero.")

    if price.isna().any():
        raise ValueError("Preço inválido ou ausente.")

    if (price < 0).any():
        raise ValueError("Preço não pode ser negativo.")

    if dates.isna().any():
        raise ValueError("Data do pedido inválida ou ausente.")
