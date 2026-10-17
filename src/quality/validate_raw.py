
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"


def validate_file(name: str, path: Path) -> bool:
    print(f"\n{'=' * 50}")
    print(f"Validando: {name}")

    if not path.exists():
        print(f"ERRO: arquivo não encontrado: {path}")
        return False

    df = pd.read_csv(path)

    has_nulls = df.isnull().any().any()
    has_duplicates = df.duplicated().any()

    print(f"Registros: {len(df)}")
    print(f"Colunas: {len(df.columns)}")
    print(f"Valores nulos: {int(df.isnull().sum().sum())}")
    print(f"Linhas duplicadas: {int(df.duplicated().sum())}")

    valid = not has_nulls and not has_duplicates

    print(f"Resultado: {'APROVADO' if valid else 'REPROVADO'}")

    return valid


def main() -> None:
    files = {
        "customers": RAW_DIR / "customers.csv",
        "orders": RAW_DIR / "orders.csv",
        "products": RAW_DIR / "products.csv",
    }

    results = [
        validate_file(name, path)
        for name, path in files.items()
    ]

    print(f"\n{'=' * 50}")
    print(f"Arquivos aprovados: {sum(results)}/{len(results)}")

    if not all(results):
        raise SystemExit("Falha na validação dos dados.")


if __name__ == "__main__":
    main()
