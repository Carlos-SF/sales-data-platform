
import pandas as pd
import pytest

from src.quality.business_rules import validate_orders


@pytest.fixture
def valid_orders():
    return pd.DataFrame({
        "quantity": [2, 3],
        "unit_price": [10.50, 25.00],
        "order_date": ["2026-01-10", "2026-01-11"],
    })


def test_valid_orders_are_accepted(valid_orders):
    assert validate_orders(valid_orders) is None


@pytest.mark.parametrize(
    ("column", "value", "expected_error"),
    [
        ("quantity", 0, "maior que zero"),
        ("quantity", -1, "maior que zero"),
        ("quantity", "abc", "Quantidade inválida"),
        ("unit_price", -0.01, "Preço não pode ser negativo"),
        ("unit_price", "abc", "Preço inválido"),
        ("order_date", "data-invalida", "Data do pedido inválida"),
    ],
)
def test_invalid_orders_are_rejected(
    valid_orders, column, value, expected_error
):
    invalid_orders = valid_orders.copy()
    invalid_orders[column] = invalid_orders[column].astype(object)
    invalid_orders.loc[0, column] = value

    with pytest.raises(ValueError, match=expected_error):
        validate_orders(invalid_orders)


def test_missing_required_column_is_rejected(valid_orders):
    invalid_orders = valid_orders.drop(columns=["quantity"])

    with pytest.raises(ValueError, match="Colunas ausentes"):
        validate_orders(invalid_orders)
