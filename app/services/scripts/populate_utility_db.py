from pathlib import Path
from app.services.utility_companies_db import import_from_csv


def main():
    seed = Path(__file__).resolve().parent.parent / "data" / "utility_companies_seed.csv"
    if not seed.exists():
        print("Seed CSV not found:", seed)
        return
    count = import_from_csv(seed)
    print(f"Imported {count} rows from {seed}")


if __name__ == "__main__":
    main()
