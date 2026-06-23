"""Download candidate CSVs of Brazilian utility companies and import into local DB.

The script tries multiple known raw URLs (GitHub raw, gists, mirrors). On first
successful CSV download it saves to a temp file and calls `import_from_csv()`
from `utility_companies_db`.

If no source is found, exits with non-zero and prints candidates tried.
"""
from pathlib import Path
import requests
import sys
from app.services.utility_companies_db import import_from_csv

SOURCES = [
    # community-maintained lists (may or may not exist)
    "https://raw.githubusercontent.com/willianjusten/energia-br/master/concessionarias.csv",
    "https://raw.githubusercontent.com/alerces/utility-providers-br/master/utility_companies.csv",
    # generic mirrors / gists - add more as needed
    "https://raw.githubusercontent.com/ramonhagata/concessionarias-br/master/concessionarias.csv",
]


def try_download(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200 and "csv" in r.headers.get("Content-Type", "") or r.text.strip().startswith(
            "codigo_ibge"
        ):
            dest.write_text(r.text, encoding="utf-8")
            return True
    except Exception:
        return False
    return False


def main():
    tmp = Path(__file__).resolve().parent.parent / "data" / "downloaded_utility_companies.csv"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tried = []
    for url in SOURCES:
        print("Trying:", url)
        tried.append(url)
        ok = try_download(url, tmp)
        if ok:
            print("Downloaded from", url)
            try:
                count = import_from_csv(tmp)
                print(f"Imported {count} rows from {url}")
                return 0
            except Exception as e:
                print("Import failed:", e)
                return 2
    print("No valid CSV found. Tried the following URLs:")
    for u in tried:
        print(" -", u)
    return 1


if __name__ == "__main__":
    sys.exit(main())
