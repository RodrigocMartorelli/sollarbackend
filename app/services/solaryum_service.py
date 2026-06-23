import json
import logging
from time import time
import uuid
from typing import Optional, Dict, Any, Tuple, List

import requests

logger = logging.getLogger(__name__)

# ========== CONFIGURAÇÃO CENTRALIZADA ==========
SOLARYUM_BASE_URL = "https://api-d0983.cloud.solaryum.com.br"
SOLARYUM_INTEGRATOR_TOKEN = "jjvMk6Rl"  # Token do integrador
SOLARYUM_COMPANY_TOKEN = "yq#q6h9y5y#tLL"  # Token da empresa
REQUEST_TIMEOUT = 120
_CACHE_TTL_SECONDS = 300
_filters_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}


class SolaryumError(Exception):
    """Exceção customizada para erros da Solaryum"""

    def __init__(self, status_code: int, message: str, details: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"[{status_code}] {message}")


def _validate_tokens(integrator_token: Optional[str], company_token: Optional[str]) -> Tuple[str, str]:
    """Valida se os tokens estão preenchidos"""
    if not integrator_token or not integrator_token.strip():
        raise SolaryumError(
            400,
            "Token do integrador vazio",
            "Informe o token do integrador (token)",
        )

    if not company_token or not company_token.strip():
        raise SolaryumError(
            400,
            "Token da empresa vazio",
            "Informe o token da empresa (tokenEmpresa)",
        )

    return integrator_token.strip(), company_token.strip()


def _build_headers(company_token: str) -> Dict[str, str]:
    """Constrói os headers para requisição à Solaryum"""
    return {
        "Authorization": company_token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _mask_sensitive_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Oculta tokens sensíveis nos logs sem perder visibilidade do payload."""
    masked = dict(params)
    if "token" in masked and masked["token"]:
        token_value = str(masked["token"])
        masked["token"] = f"{token_value[:3]}***{token_value[-3:]}" if len(token_value) > 6 else "***"
    return masked


def _format_body_for_log(body: str) -> str:
    if not body:
        return "(vazio)"
    body = body.strip()
    return body if len(body) <= 4000 else f"{body[:4000]}...(truncado)"


def _extract_message_from_response_body(response_body: str, fallback: str) -> str:
    """Extrai a mensagem real retornada pela API, se existir."""
    if not response_body:
        return fallback

    try:
        decoded = json.loads(response_body)
    except Exception:
        return response_body.strip() or fallback

    if isinstance(decoded, dict):
        for key in ("message", "mensagem", "error", "erro"):
            value = decoded.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, dict):
                nested = _extract_message_from_response_body(json.dumps(value, ensure_ascii=False), fallback)
                if nested != fallback:
                    return nested

        detail = decoded.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
        if isinstance(detail, dict):
            nested = _extract_message_from_response_body(json.dumps(detail, ensure_ascii=False), fallback)
            if nested != fallback:
                return nested

    return response_body.strip() or fallback


def _perform_get_request(label: str, path: str, params: Dict[str, Any], headers: Dict[str, str]) -> requests.Response:
    url = f"{SOLARYUM_BASE_URL}{path}"
    prepared_url = requests.Request("GET", url, params=params).prepare().url or url

    logger.info(f"{label} request iniciada")
    logger.info(f"{label} URL final: {prepared_url}")
    logger.info(f"{label} params enviados: {json.dumps(_mask_sensitive_params(params), ensure_ascii=False)}")

    response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)

    try:
        response_body = response.text.strip() if response.text else ""
    except Exception:
        response_body = "(erro ao ler resposta)"

    logger.info(f"{label} status code: {response.status_code}")
    logger.info(f"{label} response body: {_format_body_for_log(response_body)}")
    return response


def _cache_key(label: str, integrator_token: str, company_token: str) -> str:
    return json.dumps(
        {
            "label": label,
            "integrator": integrator_token,
            "company": company_token,
        },
        sort_keys=True,
        ensure_ascii=False,
    )


def _get_cached_filters(cache_key: str) -> Optional[Dict[str, Any]]:
    cached = _filters_cache.get(cache_key)
    if not cached:
        return None

    cached_at, payload = cached
    if time() - cached_at > _CACHE_TTL_SECONDS:
        _filters_cache.pop(cache_key, None)
        return None

    return payload


def _set_cached_filters(cache_key: str, payload: Dict[str, Any]) -> None:
    _filters_cache[cache_key] = (time(), payload)


def _normalize_sort_direction(sort_dir: Optional[str]) -> str:
    direction = (sort_dir or "asc").strip().lower()
    return "desc" if direction in {"desc", "descending", "down"} else "asc"


def _match_search_value(item: Any, search: str) -> bool:
    if not search:
        return True

    needle = search.strip().lower()
    if not needle:
        return True

    if isinstance(item, dict):
        for key in ("descricao", "marca", "modelo", "potencia", "idProduto", "id", "label", "nome", "value"):
            value = item.get(key)
            if value is None:
                continue
            if needle in str(value).strip().lower():
                return True
        return False

    return needle in str(item).strip().lower()


def _sort_list(items: List[Any], sort_by: Optional[str], sort_dir: Optional[str]) -> List[Any]:
    if not sort_by:
        return items

    direction = _normalize_sort_direction(sort_dir)

    def _value(item: Any) -> Any:
        if not isinstance(item, dict):
            return str(item)
        value = item.get(sort_by)
        if value is None:
            return ""
        if isinstance(value, (int, float)):
            return value
        text = str(value).strip()
        try:
            return float(text.replace(",", "."))
        except Exception:
            return text.lower()

    return sorted(items, key=_value, reverse=direction == "desc")


def _paginate_list(
    items: List[Any],
    page: int,
    limit: int,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> Dict[str, Any]:
    filtered = [item for item in items if _match_search_value(item, search or "")]
    ordered = _sort_list(filtered, sort_by, sort_dir)

    safe_page = page if page and page > 0 else 1
    safe_limit = limit if limit and limit > 0 else 10
    total = len(ordered)
    total_pages = (total + safe_limit - 1) // safe_limit if total else 0
    start = (safe_page - 1) * safe_limit
    end = start + safe_limit

    return {
        "items": ordered[start:end],
        "total": total,
        "page": safe_page,
        "limit": safe_limit,
        "pages": total_pages,
    }


def _first_non_empty_value(items, candidate_keys: Tuple[str, ...] = ("descricao", "nome", "label", "valor", "value")) -> Optional[str]:
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


def _first_power_value(items) -> Optional[float]:
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


def _looks_like_placeholder_text(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return True
    if normalized.startswith('.'):
        return True
    digits_only = normalized.replace('.', '', 1).isdigit()
    return digits_only


def _resolve_filter_identifier(
    items,
    provided_value: Optional[str],
    id_keys: Tuple[str, ...],
    description_keys: Tuple[str, ...] = ("descricao", "nome", "label"),
) -> Optional[str]:
    """Converte descrição visível em ID quando a API espera identificador."""
    if provided_value is not None:
        provided_text = str(provided_value).strip()
        if provided_text:
            normalized = provided_text.replace(",", ".")
            try:
                float(normalized)
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

    return fallback_identifier or _first_non_empty_value(items, id_keys + description_keys)


def _collect_positive_power_candidates(items) -> list:
    candidates = []
    if not isinstance(items, list):
        return candidates

    for item in items:
        power_value: Optional[float] = None
        if isinstance(item, dict):
            for key in ("potencia", "potenciaDoKit", "potenciaDoPainel", "valor"):
                value = item.get(key)
                if value is None:
                    continue
                text = str(value).strip().replace(",", ".")
                if not text:
                    continue
                try:
                    power_value = float(text)
                    break
                except ValueError:
                    continue
        else:
            text = str(item).strip().replace(",", ".")
            if text:
                try:
                    power_value = float(text)
                except ValueError:
                    power_value = None

        if power_value is not None and power_value > 0 and power_value not in candidates:
            candidates.append(power_value)

    return candidates


def _collect_identifier_candidates(
    items,
    id_keys: Tuple[str, ...],
    description_keys: Tuple[str, ...] = ("descricao", "nome", "label"),
    skip_placeholder: bool = True,
    skip_zero: bool = False,
) -> list:
    candidates = []
    if not isinstance(items, list):
        return candidates

    for item in items:
        if not isinstance(item, dict):
            text = str(item).strip()
            if text and text not in candidates:
                candidates.append(text)
            continue

        description_text = None
        for key in description_keys:
            candidate_description = item.get(key)
            if candidate_description is None:
                continue
            description_text = str(candidate_description).strip()
            if description_text:
                break

        if skip_placeholder and description_text and _looks_like_placeholder_text(description_text):
            continue

        for id_key in id_keys:
            identifier = item.get(id_key)
            if identifier is None:
                continue
            identifier_text = str(identifier).strip()
            if not identifier_text:
                continue
            if skip_zero and identifier_text in ("0", "0.0"):
                continue
            if identifier_text not in candidates:
                candidates.append(identifier_text)
            break

    return candidates


def _resolve_minimum_kit_payload(
    filters: Dict[str, Any],
    potencia_do_kit: Optional[float],
    potencia_do_painel: Optional[float],
    marca_painel: Optional[str],
    marca_inversor: Optional[str],
    telhados: Optional[str],
    ibge: Optional[str],
) -> Dict[str, Any]:
    """
    Constrói payload mínimo para MontarKits/BuscarKits.
    
    Regras:
    - IBGE é obrigatório
    - Potência: usa a fornecida ou padrão (primeira disponível)
    - Marcas (painel/inversor): enviadas como NOME (string), não ID
    - Telhados: enviado como ID (numérico)
    """
    resolved_ibge = ibge or "2800308"
    resolved_potencia = potencia_do_kit if potencia_do_kit is not None else _first_power_value(filters.get("potenciasPaineis"))

    resolved_potencia_painel = None
    if potencia_do_painel is not None:
        resolved_potencia_painel = int(potencia_do_painel) if float(potencia_do_painel).is_integer() else potencia_do_painel

    # Marcas são enviadas como NOME, não como ID
    # Se o usuário não forneceu, deixa vazio
    resolved_marca_painel = marca_painel.strip() if marca_painel and isinstance(marca_painel, str) else None
    resolved_marca_inversor = marca_inversor.strip() if marca_inversor and isinstance(marca_inversor, str) else None
    
    # Telhados continuam como ID
    resolved_telhados = None
    if telhados:
        telhados_str = str(telhados).strip()
        # Se é numérico, usa direto; se é nome, resolve para ID
        try:
            float(telhados_str)
            resolved_telhados = telhados_str
        except ValueError:
            # Tenta resolver nome para ID
            resolved_telhados = _resolve_filter_identifier(
                filters.get("tiposTelhados"),
                telhados,
                ("id",),
            )

    payload: Dict[str, Any] = {
        "ibge": resolved_ibge,
    }

    if resolved_potencia is not None:
        payload["potenciaDoKit"] = resolved_potencia
    
    # Só envia potenciaDoPainel se foi EXPLICITAMENTE fornecida
    if resolved_potencia_painel is not None:
        payload["potenciaDoPainel"] = resolved_potencia_painel
    
    if resolved_marca_painel:
        payload["marcaPainel"] = resolved_marca_painel
    if resolved_marca_inversor:
        payload["marcaInversor"] = resolved_marca_inversor
    if resolved_telhados:
        payload["telhados"] = resolved_telhados

    return payload


def _is_soft_combination_error(error: SolaryumError) -> bool:
    if error.status_code != 400:
        return False

    message = f"{error.message} {error.details or ''}".lower()
    return any(
        keyword in message
        for keyword in (
            "nenhum painel encontrado",
            "ids inválidos",
            "ids invalidos",
            "potência inválida",
            "potencia invalida",
            "combinação inválida",
            "combinacao invalida",
        )
    )


def _search_with_nearby_potencies(
    integrator_token: str,
    company_token: str,
    potencia_do_kit: Optional[float],
    potencia_do_painel: Optional[float],
    marca_painel: Optional[str],
    marca_inversor: Optional[str],
    telhados: Optional[str],
    ibge: Optional[str],
    tensao: Optional[int],
    fase: Optional[int],
    tipo_inv: Optional[int],
    cif_com_descarga: Optional[bool],
    endpoint: str = "MontarKits",
) -> list:
    """
    Tenta buscar kits com a potência exata e, se não encontrar,
    tenta valores próximos (com variação de ±0.1, ±0.2, ±0.3, etc).
    """
    if not potencia_do_kit:
        return []
    
    # Gera lista de potências a tentar: exata, +0.1, -0.1, +0.2, -0.2, +0.3, -0.3, ...
    potencies_to_try = [potencia_do_kit]
    for offset in [0.1, 0.2, 0.3, 0.4, 0.5]:
        potencies_to_try.append(potencia_do_kit + offset)
        if potencia_do_kit - offset > 0:
            potencies_to_try.append(potencia_do_kit - offset)
    
    logger.info(f"Tentando buscar com potências aproximadas: {potencies_to_try}")
    
    filtros = buscar_filtros(integrator_token=integrator_token, company_token=company_token)
    headers = _build_headers(company_token)
    
    for power_to_try in potencies_to_try:
        attempt_params = _resolve_minimum_kit_payload(
            filtros,
            power_to_try,
            potencia_do_painel or power_to_try,
            marca_painel,
            marca_inversor,
            telhados,
            ibge,
        )
        
        if tensao is not None:
            attempt_params["tensao"] = tensao
        if fase is not None:
            attempt_params["fase"] = fase
        if tipo_inv is not None:
            attempt_params["tipoInv"] = tipo_inv
        if cif_com_descarga is not None:
            attempt_params["cifComDescarga"] = cif_com_descarga
        
        try:
            params_with_token = dict(attempt_params)
            params_with_token["token"] = integrator_token
            
            response = _perform_get_request(
                endpoint,
                f"/integracaoPlataforma/{endpoint}",
                params_with_token,
                headers,
            )
            result = _handle_response(response)
            kits = result if isinstance(result, list) else [result]
            
            if kits and len(kits) > 0:
                logger.info(f"{endpoint} encontrou {len(kits)} kits com potência {power_to_try}")
                return kits
            
        except SolaryumError as error:
            if _is_soft_combination_error(error):
                logger.debug(f"{endpoint} sem resultado para potência {power_to_try}: {error.message}")
                continue
            # Se for erro diferente, continua tentando outras potências
            logger.debug(f"{endpoint} erro para potência {power_to_try}: {error.message}")
            continue
        except Exception as e:
            logger.debug(f"{endpoint} erro inesperado para potência {power_to_try}: {str(e)}")
            continue
    
    logger.info(f"{endpoint} nenhuma potência aproximada retornou resultados")
    return []



def _handle_response(response: requests.Response) -> Dict[str, Any]:
    """Trata a resposta da API Solaryum"""
    try:
        response_body = response.text.strip() if response.text else "(vazio)"
    except Exception:
        response_body = "(erro ao ler resposta)"

    if not response.ok:
        logger.error(f"Solaryum API error: status={response.status_code}, body={response_body}")
        message = _extract_message_from_response_body(
            response_body,
            f"Solaryum retornou {response.status_code}",
        )
        raise SolaryumError(
            response.status_code,
            message,
            response_body,
        )

    try:
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao decodificar resposta JSON: {response_body}")
        raise SolaryumError(
            500,
            "Resposta inválida da Solaryum",
            f"Não conseguiu decodificar JSON: {str(e)}",
        )


# ========== ENDPOINTS ==========


def buscar_filtros(
    integrator_token: Optional[str] = None,
    company_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Busca os filtros disponíveis na Solaryum.

    Args:
        integrator_token: Token do integrador (query param). Se None, usa valor default.
        company_token: Token da empresa (header Authorization). Se None, usa valor default.

    Returns:
        Dict com os filtros

    Raises:
        SolaryumError: Se falhar na requisição
    """
    # Validar ANTES de usar defaults
    if integrator_token is None:
        integrator_token = SOLARYUM_INTEGRATOR_TOKEN
    if company_token is None:
        company_token = SOLARYUM_COMPANY_TOKEN

    integrator_token, company_token = _validate_tokens(integrator_token, company_token)
    cache_key = _cache_key("buscar_filtros", integrator_token, company_token)
    cached_filters = _get_cached_filters(cache_key)
    if cached_filters is not None:
        logger.info("BuscarFiltros retornado do cache")
        return cached_filters

    params = {"token": integrator_token}
    headers = _build_headers(company_token)

    try:
        response = _perform_get_request(
            "BuscarFiltros",
            "/integracaoPlataforma/BuscarFiltros",
            params,
            headers,
        )
        result = _handle_response(response)
        if isinstance(result, dict):
            _set_cached_filters(cache_key, result)
        return result
    except requests.exceptions.Timeout:
        raise SolaryumError(504, "Timeout ao chamar Solaryum", "A requisição demorou mais de 30s")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de conexão com Solaryum: {str(e)}")
        raise SolaryumError(502, "Erro de conexão com Solaryum", str(e))
    except SolaryumError:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao chamar BuscarFiltros: {str(e)}")
        raise SolaryumError(500, "Erro ao chamar Solaryum", str(e))


def buscar_kits(
    integrator_token: Optional[str] = None,
    company_token: Optional[str] = None,
    potencia_do_kit: Optional[float] = None,
    potencia_do_painel: Optional[float] = None,
    marca_painel: Optional[str] = None,
    tensao: Optional[int] = None,
    fase: Optional[int] = None,
    marca_inversor: Optional[str] = None,
    telhados: Optional[str] = None,
    tipo_inv: Optional[int] = None,
    ibge: Optional[str] = None,
    cif_com_descarga: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> list:
    """
    Busca kits prontos na Solaryum com filtros opcionais.

    Returns:
        Lista de kits

    Raises:
        SolaryumError: Se falhar na requisição
    """
    # Validar ANTES de usar defaults
    if integrator_token is None:
        integrator_token = SOLARYUM_INTEGRATOR_TOKEN
    if company_token is None:
        company_token = SOLARYUM_COMPANY_TOKEN

    integrator_token, company_token = _validate_tokens(integrator_token, company_token)
    filtros = buscar_filtros(integrator_token=integrator_token, company_token=company_token)
    headers = _build_headers(company_token)
    attempt_params = _resolve_minimum_kit_payload(
        filtros,
        potencia_do_kit,
        potencia_do_painel,
        marca_painel,
        marca_inversor,
        telhados,
        ibge,
    )

    if tensao is not None:
        attempt_params["tensao"] = tensao
    if fase is not None:
        attempt_params["fase"] = fase
    if tipo_inv is not None:
        attempt_params["tipoInv"] = tipo_inv
    if cif_com_descarga is not None:
        attempt_params["cifComDescarga"] = cif_com_descarga

    logger.info("BuscarKits payload: %s", json.dumps(attempt_params, ensure_ascii=False))

    try:
        params_with_token = dict(attempt_params)
        params_with_token["token"] = integrator_token

        response = _perform_get_request(
            "BuscarKits",
            "/integracaoPlataforma/BuscarKits",
            params_with_token,
            headers,
        )
        result = _handle_response(response)
        return result if isinstance(result, list) else [result]
    except SolaryumError as error:
        if _is_soft_combination_error(error):
            logger.info(f"BuscarKits sem resultado: {error.message}")
            return []
        raise


def montar_kits(
    integrator_token: Optional[str] = None,
    company_token: Optional[str] = None,
    potencia_do_kit: Optional[float] = None,
    potencia_do_painel: Optional[float] = None,
    marca_painel: Optional[str] = None,
    tensao: Optional[int] = None,
    fase: Optional[int] = None,
    marca_inversor: Optional[str] = None,
    telhados: Optional[str] = None,
    tipo_inv: Optional[int] = None,
    ibge: Optional[str] = None,
    cif_com_descarga: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> list:
    """
    Monta kits personalizados na Solaryum com filtros opcionais.

    Returns:
        Lista de kits montados

    Raises:
        SolaryumError: Se falhar na requisição
    """
    # Validar ANTES de usar defaults
    if integrator_token is None:
        integrator_token = SOLARYUM_INTEGRATOR_TOKEN
    if company_token is None:
        company_token = SOLARYUM_COMPANY_TOKEN

    integrator_token, company_token = _validate_tokens(integrator_token, company_token)
    filtros = buscar_filtros(integrator_token=integrator_token, company_token=company_token)
    headers = _build_headers(company_token)
    attempt_params = _resolve_minimum_kit_payload(
        filtros,
        potencia_do_kit,
        potencia_do_painel,
        marca_painel,
        marca_inversor,
        telhados,
        ibge,
    )

    if tensao is not None:
        attempt_params["tensao"] = tensao
    if fase is not None:
        attempt_params["fase"] = fase
    if tipo_inv is not None:
        attempt_params["tipoInv"] = tipo_inv
    if cif_com_descarga is not None:
        attempt_params["cifComDescarga"] = cif_com_descarga

    logger.info("MontarKits payload único: %s", json.dumps(attempt_params, ensure_ascii=False))

    # Tenta a requisição com um retry simples em caso de timeout.
    params_with_token = dict(attempt_params)
    params_with_token["token"] = integrator_token

    last_exception = None
    for attempt in range(2):
        request_id = uuid.uuid4().hex[:8]
        # Preparar URL para log completo
        try:
            prepared_url = requests.Request(
                "GET",
                f"{SOLARYUM_BASE_URL}/integracaoPlataforma/MontarKits",
                params=params_with_token,
            ).prepare().url
        except Exception:
            prepared_url = f"{SOLARYUM_BASE_URL}/integracaoPlataforma/MontarKits"

        # Mascarar headers para logs
        try:
            masked_headers = dict(headers)
            if "Authorization" in masked_headers and masked_headers["Authorization"]:
                token_value = str(masked_headers["Authorization"])
                masked_headers["Authorization"] = f"{token_value[:3]}***{token_value[-3:]}" if len(token_value) > 6 else "***"
        except Exception:
            masked_headers = {k: "***" for k in (headers or {}).keys()}

        logger.info(
            "MontarKits request_id=%s attempt=%d prepared_url=%s headers=%s params=%s",
            request_id,
            attempt + 1,
            prepared_url,
            json.dumps(masked_headers, ensure_ascii=False),
            json.dumps(_mask_sensitive_params(params_with_token), ensure_ascii=False),
        )

        start = time()
        try:
            response = _perform_get_request(
                "MontarKits",
                "/integracaoPlataforma/MontarKits",
                params_with_token,
                headers,
            )
            elapsed = time() - start
            logger.info("MontarKits request_id=%s attempt=%d completed in %.2fs", request_id, attempt + 1, elapsed)
            result = _handle_response(response)
            return result if isinstance(result, list) else [result]
        except requests.exceptions.Timeout as e:
            logger.warning(f"MontarKits attempt {attempt+1} timeout: {str(e)}")
            last_exception = e
            # tenta novamente uma vez; se falhar de novo, converte para SolaryumError 504
            continue
        except requests.exceptions.ConnectionError as e:
            logger.error(f"MontarKits connection error: {str(e)}")
            raise SolaryumError(502, "Erro de conexão com Solaryum", str(e))
        except SolaryumError as error:
            if _is_soft_combination_error(error):
                logger.info(f"MontarKits sem resultado: {error.message}")
                return []
            raise

    # Se chegou aqui é porque os attempts falharam por timeout
    logger.error("MontarKits falhou por timeout após tentativas")
    raise SolaryumError(504, "Timeout ao chamar Solaryum", "A requisição demorou mais de 30s")
