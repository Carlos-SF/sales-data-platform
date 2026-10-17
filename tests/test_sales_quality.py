
from pathlib import Path

import pandas as pd
import pytest

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "silver"


@pytest.fixture(scope="module")
def datasets():
    """Carrega os arquivos Silver para os testes."""
    required_files = ["orders.csv", "customers.csv", "products.csv"]

    for filename in required_files:
        path = DATA_DIR / filename
        if not path.exists():
            pytest.fail(f"Arquivo Silver não encontrado: {path}")

    return {
        "orders": pd.read_csv(DATA_DIR / "orders.csv"),
        "customers": pd.read_csv(DATA_DIR / "customers.csv"),
        "products": pd.read_csv(DATA_DIR / "products.csv"),
    }


def test_ids_are_unique(datasets):
    """Verifica se as chaves primárias são únicas."""
    assert datasets["orders"]["order_id"].is_unique
    assert datasets["customers"]["customer_id"].is_unique
    assert datasets["products"]["product_id"].is_unique


def test_orders_have_valid_references(datasets):
    """Verifica se os pedidos apontam para clientes e produtos existentes."""
    orders = datasets["orders"]
    customers = datasets["customers"]
    products = datasets["products"]

    assert orders["customer_id"].isin(customers["customer_id"]).all()
    assert orders["product_id"].isin(products["product_id"]).all()


def test_business_rules(datasets):
    """Valida quantidades, preços e datas dos pedidos."""
    orders = datasets["orders"]

    quantity = pd.to_numeric(orders["quantity"], errors="coerce")
    price = pd.to_numeric(orders["unit_price"], errors="coerce")
    dates = pd.to_datetime(orders["order_date"], errors="coerce")

    assert quantity.notna().all(), "Existem quantidades inválidas."
    assert (quantity > 0).all(), "Existem quantidades menores ou iguais a zero."

    assert price.notna().all(), "Existem preços inválidos."
    assert (price >= 0).all(), "Existem preços negativos."

    assert dates.notna().all(), "Existem datas inválidas."


def test_financial_reconciliation(datasets):
    """Confere o valor bruto dos pedidos da Silver."""
    orders = datasets["orders"]

    quantity = pd.to_numeric(orders["quantity"], errors="coerce")
    price = pd.to_numeric(orders["unit_price"], errors="coerce")
    total = (quantity * price).sum()

    assert len(orders) == 100_000
    assert total == pytest.approx(811_884_574.08, abs=0.01)


def test_completed_orders_value(datasets):
    """Confere o valor financeiro dos pedidos concluídos."""
    orders = datasets["orders"]
    completed = orders[
        orders["status"].astype(str).str.strip().str.lower() == "completed"
    ]

    total = (
        pd.to_numeric(completed["quantity"], errors="coerce")
        * pd.to_numeric(completed["unit_price"], errors="coerce")
    ).sum()

    assert total == pytest.approx(586_385_508.02, abs=0.01)
