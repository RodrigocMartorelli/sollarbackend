#!/usr/bin/env python3
"""
Script de teste rápido para validar a integração Solaryum/Fotus

Uso:
    python test_solaryum_integration.py

Este script testa:
    1. Validação de tokens
    2. Requisição a BuscarFiltros
    3. Tratamento de erros
"""

import sys
from app.services.solaryum_service import (
    buscar_filtros,
    buscar_kits,
    montar_kits,
    SolaryumError,
)

# Cores para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def _first_non_empty_value(items, candidate_keys=("descricao", "nome", "label", "valor", "value")):
    if not isinstance(items, list):
        return None

    for item in items:
        if isinstance(item, dict):
            for key in candidate_keys:
                value = item.get(key)
                if value is not None:
                    text = str(value).strip()
                    if text:
                        return text
        else:
            text = str(item).strip()
            if text:
                return text

    return None


def _first_power_value(items):
    if not isinstance(items, list):
        return None

    for item in items:
        if isinstance(item, dict):
            for key in ("potencia", "potenciaDoKit", "potenciaDoPainel", "valor"):
                value = item.get(key)
                if value is None:
                    continue
                text = str(value).strip().replace(",", ".")
                if not text:
                    continue
                try:
                    power = float(text)
                    if power > 0:
                        return power
                except ValueError:
                    continue
        else:
            text = str(item).strip().replace(",", ".")
            if not text:
                continue
            try:
                power = float(text)
                if power > 0:
                    return power
            except ValueError:
                continue

    return None


def _resolve_filter_identifier(items, provided_value=None, id_keys=("idMarca", "id"), description_keys=("descricao", "nome", "label")):
    def _looks_like_placeholder_text(text):
        normalized = text.strip()
        if not normalized:
            return True
        if normalized.startswith('.'):
            return True
        return normalized.replace('.', '', 1).isdigit()

    if provided_value is not None:
        provided_text = str(provided_value).strip()
        if provided_text:
            try:
                float(provided_text.replace(',', '.'))
                return provided_text
            except ValueError:
                pass

            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    for key in description_keys:
                        candidate = item.get(key)
                        if candidate is not None and str(candidate).strip() == provided_text:
                            for id_key in id_keys:
                                identifier = item.get(id_key)
                                if identifier is not None:
                                    identifier_text = str(identifier).strip()
                                    if identifier_text:
                                        return identifier_text
            return provided_text

    if not isinstance(items, list):
        return None

    fallback_identifier = None
    for item in items:
        if not isinstance(item, dict):
            text = str(item).strip()
            if text and fallback_identifier is None:
                fallback_identifier = text
            continue

        for key in description_keys:
            candidate_description = item.get(key)
            if candidate_description is None:
                continue
            description_text = str(candidate_description).strip()
            if not description_text or _looks_like_placeholder_text(description_text):
                continue

            for id_key in id_keys:
                identifier = item.get(id_key)
                if identifier is not None:
                    identifier_text = str(identifier).strip()
                    if identifier_text:
                        return identifier_text

            return description_text

        if fallback_identifier is None:
            for id_key in id_keys:
                identifier = item.get(id_key)
                if identifier is not None:
                    identifier_text = str(identifier).strip()
                    if identifier_text:
                        fallback_identifier = identifier_text
                        break

    return fallback_identifier


def _build_minimum_payload(filters):
    power = _first_power_value(filters.get("potenciasPaineis"))
    roof_candidates = [
        value
        for value in (
            str(item.get("id")).strip()
            for item in filters.get("tiposTelhados", [])
            if isinstance(item, dict) and item.get("id") is not None
        )
        if value and value not in ("0", "0.0")
    ]
    payload = {
        "ibge": "2800308",
        "potenciaDoKit": power,
        "potenciaDoPainel": power,
        "marcaPainel": _resolve_filter_identifier(filters.get("marcasPaineis"), id_keys=("idMarca", "id")),
        "marcaInversor": _resolve_filter_identifier(filters.get("marcasInversores"), id_keys=("idMarca", "id")),
        "telhados": roof_candidates[0] if roof_candidates else None,
    }

    return {key: value for key, value in payload.items() if value is not None and str(value).strip() != ""}


def test_token_validation():
    """Testa validação de tokens vazios"""
    print(f"\n{YELLOW}Teste 1: Validação de tokens{RESET}")

    try:
        buscar_filtros(integrator_token="", company_token="token_valido")
        print(f"{RED}❌ Deveria lançar erro para token integrador vazio{RESET}")
        return False
    except SolaryumError as e:
        if "integrador" in e.message.lower() and e.status_code == 400:
            print(f"{GREEN}✅ Token integrador vazio detectado{RESET}")
        else:
            print(f"{RED}❌ Erro incorreto: {e.message}{RESET}")
            return False

    try:
        buscar_filtros(integrator_token="token_valido", company_token="")
        print(f"{RED}❌ Deveria lançar erro para token empresa vazio{RESET}")
        return False
    except SolaryumError as e:
        if "empresa" in e.message.lower() and e.status_code == 400:
            print(f"{GREEN}✅ Token empresa vazio detectado{RESET}")
        else:
            print(f"{RED}❌ Erro incorreto: {e.message}{RESET}")
            return False

    return True


def test_buscar_filtros():
    """Testa requisição a BuscarFiltros com tokens válidos"""
    print(f"\n{YELLOW}Teste 2: Buscar Filtros (requisição real){RESET}")

    try:
        result = buscar_filtros()
        if result and isinstance(result, dict):
            print(f"{GREEN}✅ Resposta recebida: {len(result)} campos{RESET}")
            for key in result.keys():
                count = len(result[key]) if isinstance(result[key], list) else "?"
                print(f"   - {key}: {count}")
            return True
        else:
            print(f"{RED}❌ Resposta inválida{RESET}")
            return False
    except SolaryumError as e:
        print(f"{RED}❌ Erro: {e.message}{RESET}")
        if e.details:
            print(f"   Detalhes: {e.details[:200]}...")
        return False
    except Exception as e:
        print(f"{RED}❌ Erro inesperado: {str(e)}{RESET}")
        return False


def test_buscar_kits():
    """Testa requisição a BuscarKits com token válido"""
    print(f"\n{YELLOW}Teste 3: Buscar Kits (requisição real){RESET}")

    try:
        filters = buscar_filtros()
        payload = _build_minimum_payload(filters)
        print(f"   Payload mínimo: {payload}")

        result = buscar_kits(
            potencia_do_kit=payload.get("potenciaDoKit"),
            marca_painel=payload.get("marcaPainel"),
            marca_inversor=payload.get("marcaInversor"),
            telhados=payload.get("telhados"),
            ibge=payload.get("ibge"),
        )
        if isinstance(result, list):
            print(f"{GREEN}✅ Resposta recebida: {len(result)} kits{RESET}")
            if len(result) > 0:
                print(f"   Primeiro kit: {str(result[0])[:100]}...")
            return True
        else:
            print(f"{RED}❌ Resposta inválida (esperado lista){RESET}")
            return False
    except SolaryumError as e:
        print(f"{RED}❌ Erro: {e.message}{RESET}")
        if e.details:
            print(f"   Detalhes: {e.details[:200]}...")
        return False
    except Exception as e:
        print(f"{RED}❌ Erro inesperado: {str(e)}{RESET}")
        return False


def test_montar_kits():
    """Testa requisição a MontarKits com payload mínimo válido"""
    print(f"\n{YELLOW}Teste 4: Montar Kits (requisição real){RESET}")

    try:
        filters = buscar_filtros()
        payload = _build_minimum_payload(filters)
        print(f"   Payload mínimo: {payload}")

        result = montar_kits(
            potencia_do_kit=payload.get("potenciaDoKit"),
            marca_painel=payload.get("marcaPainel"),
            marca_inversor=payload.get("marcaInversor"),
            telhados=payload.get("telhados"),
            ibge=payload.get("ibge"),
        )
        if isinstance(result, list):
            print(f"{GREEN}✅ Resposta recebida: {len(result)} kits{RESET}")
            if len(result) > 0:
                print(f"   Primeiro kit: {str(result[0])[:100]}...")
            return True
        else:
            print(f"{RED}❌ Resposta inválida (esperado lista){RESET}")
            return False
    except SolaryumError as e:
        print(f"{RED}❌ Erro: {e.message}{RESET}")
        if e.details:
            print(f"   Detalhes: {e.details[:200]}...")
        return False
    except Exception as e:
        print(f"{RED}❌ Erro inesperado: {str(e)}{RESET}")
        return False


def main():
    """Executa todos os testes"""
    print(f"\n{'=' * 60}")
    print(f"Teste de Integração Solaryum/Fotus")
    print(f"{'=' * 60}")

    results = []

    results.append(("Validação de tokens", test_token_validation()))
    results.append(("Buscar Filtros", test_buscar_filtros()))
    results.append(("Buscar Kits", test_buscar_kits()))
    results.append(("Montar Kits", test_montar_kits()))

    print(f"\n{'=' * 60}")
    print(f"Resumo dos Testes:")
    print(f"{'=' * 60}")

    passed = 0
    failed = 0

    for name, result in results:
        if result:
            print(f"{GREEN}✅ {name}{RESET}")
            passed += 1
        else:
            print(f"{RED}❌ {name}{RESET}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    print(f"{'=' * 60}\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
