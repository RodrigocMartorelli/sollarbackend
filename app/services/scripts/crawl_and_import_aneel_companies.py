"""Crawl ANEEL ArcGIS Hub search pages to extract distributor names and import into DB.

This script requests the search page with tag 'distribuicao' and extracts
uppercase tokens that look like company codes (e.g., ENEL_SP, LIGHT, ELETROACRE)
and also tries to extract words from document titles. It inserts discovered
names into the `companies` table via `utility_companies_db.insert_company_name`.
"""
from pathlib import Path
import re
import time
import requests
from app.services.utility_companies_db import insert_company_name

BASE = "https://dadosabertos-aneel.opendata.arcgis.com/search?tags=distribuicao"


def extract_names_from_html(html: str) -> set[str]:
    names = set()
    # find all-caps sequences (company-style) inside tags
    for m in re.finditer(r">\s*([A-Z][A-Z &]{2,50}[A-Z])\s*<", html):
        tok = m.group(1).strip()
        # ignore tokens with digits or obvious HTML tokens
        if re.search(r"\d", tok):
            continue
        # require at least one vowel to avoid hex-like codes
        if not re.search(r"[AEIOU]", tok):
            continue
        names.add(re.sub(r"\s{2,}", " ", tok))

    # also look for title/alt attributes
    for m in re.finditer(r'(?:title|alt|aria-label)="([^"]{3,60})"', html):
        tok = m.group(1).strip()
        if len(tok) > 2 and tok.isupper() and not re.search(r"\d", tok) and re.search(r"[AEIOU]", tok):
            names.add(re.sub(r"_", " ", tok))

    # fallback: capture words like Enel, Energisa (capitalized)
    for m in re.finditer(r">\s*([A-Z][a-z]{2,30}(?: [A-Z][a-z]{2,30})?)\s*<", html):
        tok = m.group(1).strip()
        if len(tok) > 3 and not re.search(r"\d", tok):
            names.add(tok)

    # final cleanup
    cleaned = set()
    stopwords = {"DOCUMENT", "DEVELOPMENT", "DATA", "SITE", "TESTING", "URL", "DOMAIN"}
    for n in names:
        n2 = n.strip()
        if n2.upper() in stopwords:
            continue
        if 2 < len(n2) <= 40:
            cleaned.add(n2)
    return cleaned


def main():
    discovered = set()
    # try first 20 pages (the hub may paginate with &page=N)
    for page in range(1, 21):
        url = BASE + (f"&page={page}" if page > 1 else "")
        print("Fetching", url)
        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                print("non-200", r.status_code)
                break
            names = extract_names_from_html(r.text)
            new = names - discovered
            print(f"Found {len(names)} names, {len(new)} new")
            discovered |= names
            # polite pause
            time.sleep(0.5)
            # stop early if many discovered
            if len(discovered) > 400:
                break
        except Exception as e:
            print("error fetching", e)
            break

    print(f"Total discovered candidate names: {len(discovered)}")
    if not discovered:
        return 1

    # insert into DB
    for name in sorted(discovered):
        try:
            insert_company_name(name)
        except Exception as e:
            print("insert failed for", name, e)

    print("Imported candidate company names into DB (companies table).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
