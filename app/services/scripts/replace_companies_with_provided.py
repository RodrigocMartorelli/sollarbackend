"""Replace `companies` table contents with the provided list of distributors.

This script wipes the `companies` table and inserts each `sigla` from the
provided list as the `name` value.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from app.services.utility_companies_db import _get_conn, insert_company_name

DATA = [
  { "sigla": "AMAZONAS ENERGIA", "nome": "Amazonas Energia S.A.", "uf": "AM", "regiao": "NO" },
  { "sigla": "CELESC", "nome": "Celesc Distribuição S.A.", "uf": "SC", "regiao": "SU" },
  { "sigla": "CEMIG", "nome": "Cemig Distribuição S.A.", "uf": "MG", "regiao": "SE" },
  { "sigla": "COPEL", "nome": "Copel Distribuição S.A.", "uf": "PR", "regiao": "SU" },
  { "sigla": "CPFL PAULISTA", "nome": "Companhia Paulista de Força e Luz", "uf": "SP", "regiao": "SE" },
  { "sigla": "CPFL PIRATININGA", "nome": "Companhia Piratininga de Força e Luz", "uf": "SP", "regiao": "SE" },
  { "sigla": "CPFL SANTA CRUZ", "nome": "Companhia Jaguari de Energia", "uf": "SP", "regiao": "SE" },
  { "sigla": "DME", "nome": "DME Distribuição S.A.", "uf": "MG", "regiao": "SE" },
  { "sigla": "EDP ES", "nome": "EDP Espírito Santo Distribuição de Energia S.A.", "uf": "ES", "regiao": "SE" },
  { "sigla": "EDP SP", "nome": "EDP São Paulo Distribuição de Energia S.A.", "uf": "SP", "regiao": "SE" },
  { "sigla": "ENEL CE", "nome": "Companhia Energética do Ceará", "uf": "CE", "regiao": "NE" },
  { "sigla": "ENEL RJ", "nome": "Ampla Energia e Serviços S.A.", "uf": "RJ", "regiao": "SE" },
  { "sigla": "ENEL SP", "nome": "Eletropaulo Metropolitana Eletricidade de São Paulo S.A.", "uf": "SP", "regiao": "SE" },
  { "sigla": "ENERGISA AC", "nome": "Energisa Acre - Distribuidora de Energia S.A.", "uf": "AC", "regiao": "NO" },
  { "sigla": "ENERGISA MG", "nome": "Energisa Minas Rio - Distribuidora de Energia S.A.", "uf": "MG", "regiao": "SE" },
  { "sigla": "ENERGISA MS", "nome": "Energisa Mato Grosso do Sul - Distribuidora de Energia S.A.", "uf": "MS", "regiao": "CO" },
  { "sigla": "ENERGISA MT", "nome": "Energisa Mato Grosso - Distribuidora de Energia S.A.", "uf": "MT", "regiao": "CO" },
  { "sigla": "ENERGISA PB", "nome": "Energisa Paraíba - Distribuidora de Energia S.A.", "uf": "PB", "regiao": "NE" },
  { "sigla": "ENERGISA RO", "nome": "Energisa Rondônia - Distribuidora de Energia S.A.", "uf": "RO", "regiao": "NO" },
  { "sigla": "ENERGISA SE", "nome": "Energisa Sergipe - Distribuidora de Energia S.A.", "uf": "SE", "regiao": "NE" },
  { "sigla": "ENERGISA SS", "nome": "Energisa Sul-Sudeste - Distribuidora de Energia S.A.", "uf": "SP", "regiao": "SE" },
  { "sigla": "ENERGISA TO", "nome": "Energisa Tocantins Distribuidora de Energia S.A.", "uf": "TO", "regiao": "NO" },
  { "sigla": "EQUATORIAL AL", "nome": "Equatorial Alagoas Distribuidora de Energia S.A.", "uf": "AL", "regiao": "NE" },
  { "sigla": "EQUATORIAL AP", "nome": "Equatorial Amapá Distribuidora de Energia S.A.", "uf": "AP", "regiao": "NO" },
  { "sigla": "EQUATORIAL GO", "nome": "Equatorial Goiás Distribuidora de Energia S.A.", "uf": "GO", "regiao": "CO" },
  { "sigla": "EQUATORIAL MA", "nome": "Equatorial Maranhão Distribuidora de Energia S.A.", "uf": "MA", "regiao": "NE" },
  { "sigla": "EQUATORIAL PA", "nome": "Equatorial Pará Distribuidora de Energia S.A.", "uf": "PA", "regiao": "NO" },
  { "sigla": "EQUATORIAL PI", "nome": "Equatorial Piauí Distribuidora de Energia S.A.", "uf": "PI", "regiao": "NE" },
  { "sigla": "EQUATORIAL RS", "nome": "Equatorial Rio Grande do Sul (antiga CEEE-D)", "uf": "RS", "regiao": "SU" },
  { "sigla": "LIGHT SESA", "nome": "Light Serviços de Eletricidade S.A.", "uf": "RJ", "regiao": "SE" },
  { "sigla": "NEOENERGIA BRASÍLIA", "nome": "Neoenergia Distribuição Brasília S.A.", "uf": "DF", "regiao": "CO" },
  { "sigla": "NEOENERGIA COELBA", "nome": "Companhia de Eletricidade do Estado da Bahia Coelba", "uf": "BA", "regiao": "NE" },
  { "sigla": "NEOENERGIA COSERN", "nome": "Companhia Energética do Rio Grande do Norte Cosern", "uf": "RN", "regiao": "NE" },
  { "sigla": "NEOENERGIA ELEKTRO", "nome": "Elektro Redes S.A.", "uf": "SP", "regiao": "SE" },
  { "sigla": "NEOENERGIA PERNAMBUCO", "nome": "Companhia Energética de Pernambuco (antiga Celpe)", "uf": "PE", "regiao": "NE" },
  { "sigla": "RGE", "nome": "RGE Sul Distribuidora de Energia S.A.", "uf": "RS", "regiao": "SU" },
  { "sigla": "RORAIMA ENERGIA", "nome": "Roraima Energia S.A.", "uf": "RR", "regiao": "NO" },
  { "sigla": "SULGIPE", "nome": "Companhia Sul Sergipe de Eletricidade", "uf": "SE", "regiao": "NE" }
]


def main() -> int:
    # ensure DB and schema
    conn = _get_conn(create=True)
    cur = conn.cursor()
    # wipe existing companies
    cur.execute("DELETE FROM companies")
    conn.commit()
    conn.close()

    # insert provided siglas as names
    for item in DATA:
        sigla = item.get("sigla")
        if sigla:
            try:
                insert_company_name(sigla.strip())
            except Exception as e:
                print("failed to insert", sigla, e)

    # report count
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM companies")
    cnt = cur.fetchone()[0]
    conn.close()
    print(f"Inserted {cnt} companies into companies table.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
