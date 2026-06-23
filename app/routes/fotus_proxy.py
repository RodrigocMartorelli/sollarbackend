import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.models import User
from app.security import decrypt_data, encrypt_data, get_current_user
from app.services.solaryum_service import (
    SOLARYUM_COMPANY_TOKEN,
    SOLARYUM_INTEGRATOR_TOKEN,
    SolaryumError,
    buscar_filtros,
    buscar_kits,
    montar_kits,
)

router = APIRouter(prefix="/fotus", tags=["fotus"])
logger = logging.getLogger(__name__)


class FotusFiltersBody(BaseModel):
    pass


class FotusKitsBody(BaseModel):
    potenciaDoKit: Optional[float] = None
    potenciaDoPainel: Optional[float] = None
    marcaPainel: Optional[str] = None
    tensao: Optional[int] = None
    fase: Optional[int] = None
    marcaInversor: Optional[str] = None
    telhados: Optional[str] = None
    tipoInv: Optional[int] = None
    ibge: Optional[str] = None
    cifComDescarga: Optional[bool] = None
    search: Optional[str] = None
    page: int = 1
    limit: int = 20
    sortBy: Optional[str] = None
    sortDir: Optional[str] = None


def _handle_solaryum_error(error: SolaryumError) -> HTTPException:
    logger.error("SolaryumError: %s - %s", error.message, error.details)

    if error.status_code == 400:
        return HTTPException(
            status_code=400,
            detail={"error": "Requisição inválida", "message": error.message, "details": error.details},
        )
    if error.status_code in (401, 403):
        return HTTPException(
            status_code=403,
            detail={"error": "Acesso negado", "message": "Credenciais Fotus indisponíveis", "details": error.details},
        )
    if error.status_code == 404:
        return HTTPException(
            status_code=404,
            detail={"error": "Recurso não encontrado", "message": error.message, "details": error.details},
        )
    if error.status_code in (502, 503, 504):
        return HTTPException(
            status_code=502,
            detail={"error": "Serviço indisponível", "message": "A Solaryum está temporariamente indisponível", "details": error.details},
        )

    return HTTPException(
        status_code=500,
        detail={"error": "Erro ao chamar Solaryum", "message": error.message, "details": error.details},
    )


def _record_error(db: Session, page: str, message: str, details: str = None) -> int:
    try:
        err = models.ErrorLog(
            page_name=page,
            error_message=message[:1024],
            stack_trace=(details or "")[:10000],
        )
        db.add(err)
        db.commit()
        db.refresh(err)
        logger.info("Erro registrado id=%s page=%s", err.id, page)
        return err.id
    except Exception as exc:
        logger.error("Falha ao gravar erro no DB: %s", str(exc))
        return -1


def _paginate_items(items, page: int, limit: int):
    safe_page = page if page and page > 0 else 1
    safe_limit = limit if limit and limit > 0 else 20
    total = len(items)
    pages = (total + safe_limit - 1) // safe_limit if total else 0
    start = (safe_page - 1) * safe_limit
    end = start + safe_limit
    return {"items": items[start:end], "total": total, "page": safe_page, "limit": safe_limit, "pages": pages}


def _filter_sort_paginate(
    items,
    *,
    search: Optional[str],
    search_fields: tuple[str, ...],
    sort_by: Optional[str],
    sort_dir: Optional[str],
    page: int,
    limit: int,
):
    filtered = items
    if search:
        search_term = search.strip().lower()
        if search_term:
            filtered = [
                item
                for item in filtered
                if any(search_term in str(item.get(field, "")).lower() for field in search_fields)
            ]

    if sort_by:
        reverse = (sort_dir or "asc").lower() in ("desc", "descending", "down")

        def _sort_value(item):
            value = item.get(sort_by)
            if isinstance(value, (int, float)):
                return value
            if value is None:
                return ""
            text = str(value).strip()
            try:
                return float(text.replace(",", "."))
            except Exception:
                return text.lower()

        filtered = sorted(filtered, key=_sort_value, reverse=reverse)

    window = _paginate_items(filtered, page, limit)
    return {
        "items": window["items"],
        "pagination": {
            "page": window["page"],
            "limit": window["limit"],
            "total": window["total"],
            "pages": window["pages"],
        },
    }


def _get_fotus_credentials(db: Session) -> tuple[str, str]:
    credential = db.query(models.FotusCredential).order_by(models.FotusCredential.id.asc()).first()
    if credential is None:
        credential = models.FotusCredential(
            integrator_token=encrypt_data(SOLARYUM_INTEGRATOR_TOKEN),
            company_token=encrypt_data(SOLARYUM_COMPANY_TOKEN),
        )
        db.add(credential)
        db.commit()
        db.refresh(credential)

    try:
        integrator_token = decrypt_data(credential.integrator_token)
        company_token = decrypt_data(credential.company_token)
    except Exception:
        integrator_token = SOLARYUM_INTEGRATOR_TOKEN
        company_token = SOLARYUM_COMPANY_TOKEN

    return integrator_token, company_token


@router.get("/BuscarFiltros")
async def endpoint_buscar_filtros(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await endpoint_buscar_filtros_post(body=FotusFiltersBody(), db=db, current_user=current_user)


@router.post("/BuscarFiltros")
async def endpoint_buscar_filtros_post(
    body: FotusFiltersBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        integrator_token, company_token = _get_fotus_credentials(db)
        return buscar_filtros(integrator_token=integrator_token, company_token=company_token)
    except SolaryumError as error:
        raise _handle_solaryum_error(error)
    except Exception as exc:
        logger.error("Erro inesperado em BuscarFiltros: %s", str(exc))
        raise HTTPException(
            status_code=500,
            detail={"error": "Erro interno", "message": "Ocorreu um erro ao processar sua requisição"},
        )


@router.get("/BuscarKits")
async def endpoint_buscar_kits(
    potenciaDoKit: Optional[float] = Query(None),
    potenciaDoPainel: Optional[float] = Query(None),
    marcaPainel: Optional[str] = Query(None),
    tensao: Optional[int] = Query(None),
    fase: Optional[int] = Query(None),
    marcaInversor: Optional[str] = Query(None),
    telhados: Optional[str] = Query(None),
    tipoInv: Optional[int] = Query(None),
    ibge: Optional[str] = Query(None),
    cifComDescarga: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    sortBy: Optional[str] = Query(None),
    sortDir: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    body = FotusKitsBody.model_validate(
        {
            "potenciaDoKit": potenciaDoKit,
            "potenciaDoPainel": potenciaDoPainel,
            "marcaPainel": marcaPainel,
            "tensao": tensao,
            "fase": fase,
            "marcaInversor": marcaInversor,
            "telhados": telhados,
            "tipoInv": tipoInv,
            "ibge": ibge,
            "cifComDescarga": cifComDescarga,
            "search": search,
            "page": page,
            "limit": limit,
            "sortBy": sortBy,
            "sortDir": sortDir,
        }
    )
    return await endpoint_buscar_kits_post(body=body, db=db, current_user=current_user)


@router.post("/BuscarKits")
async def endpoint_buscar_kits_post(
    body: FotusKitsBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        integrator_token, company_token = _get_fotus_credentials(db)
        result = buscar_kits(
            integrator_token=integrator_token,
            company_token=company_token,
            potencia_do_kit=body.potenciaDoKit,
            potencia_do_painel=body.potenciaDoPainel,
            marca_painel=body.marcaPainel,
            tensao=body.tensao,
            fase=body.fase,
            marca_inversor=body.marcaInversor,
            telhados=body.telhados,
            tipo_inv=body.tipoInv,
            ibge=body.ibge,
            cif_com_descarga=body.cifComDescarga,
        )

        if isinstance(result, list) and not result:
            return {"message": "Kit para esse projeto está indisponível.", "kits": []}

        if isinstance(result, list):
            return _filter_sort_paginate(
                result,
                search=body.search,
                search_fields=("descricao", "marca", "modelo", "potencia", "idProduto"),
                sort_by=body.sortBy,
                sort_dir=body.sortDir,
                page=body.page,
                limit=body.limit,
            )

        return {"items": [result], "pagination": {"page": body.page, "limit": body.limit, "total": 1, "pages": 1}}
    except SolaryumError as error:
        try:
            _record_error(db, "BuscarKits", error.message, error.details)
        except Exception:
            logger.exception("Erro ao registrar SolaryumError")
        raise _handle_solaryum_error(error)
    except Exception as exc:
        logger.error("Erro inesperado em BuscarKits POST: %s", str(exc))
        try:
            _record_error(db, "BuscarKits", str(exc), None)
        except Exception:
            logger.exception("Erro ao registrar exceção inesperada")
        raise HTTPException(
            status_code=500,
            detail={"error": "Erro interno", "message": "Ocorreu um erro ao processar sua requisição"},
        )


@router.get("/MontarKits")
async def endpoint_montar_kits(
    potenciaDoKit: Optional[float] = Query(None),
    potenciaDoPainel: Optional[float] = Query(None),
    marcaPainel: Optional[str] = Query(None),
    tensao: Optional[int] = Query(None),
    fase: Optional[int] = Query(None),
    marcaInversor: Optional[str] = Query(None),
    telhados: Optional[str] = Query(None),
    tipoInv: Optional[int] = Query(None),
    ibge: Optional[str] = Query(None),
    cifComDescarga: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    sortBy: Optional[str] = Query(None),
    sortDir: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    body = FotusKitsBody.model_validate(
        {
            "potenciaDoKit": potenciaDoKit,
            "potenciaDoPainel": potenciaDoPainel,
            "marcaPainel": marcaPainel,
            "tensao": tensao,
            "fase": fase,
            "marcaInversor": marcaInversor,
            "telhados": telhados,
            "tipoInv": tipoInv,
            "ibge": ibge,
            "cifComDescarga": cifComDescarga,
            "search": search,
            "page": page,
            "limit": limit,
            "sortBy": sortBy,
            "sortDir": sortDir,
        }
    )
    return await endpoint_montar_kits_post(body=body, db=db, current_user=current_user)


@router.post("/MontarKits")
async def endpoint_montar_kits_post(
    body: FotusKitsBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        integrator_token, company_token = _get_fotus_credentials(db)
        result = montar_kits(
            integrator_token=integrator_token,
            company_token=company_token,
            potencia_do_kit=body.potenciaDoKit,
            potencia_do_painel=body.potenciaDoPainel,
            marca_painel=body.marcaPainel,
            tensao=body.tensao,
            fase=body.fase,
            marca_inversor=body.marcaInversor,
            telhados=body.telhados,
            tipo_inv=body.tipoInv,
            ibge=body.ibge,
            cif_com_descarga=body.cifComDescarga,
        )

        if isinstance(result, list) and not result:
            return {"message": "Kit para esse projeto está indisponível.", "kits": []}

        if isinstance(result, list):
            return _filter_sort_paginate(
                result,
                search=body.search,
                search_fields=("descricao", "marca", "modelo", "potencia", "precoVenda"),
                sort_by=body.sortBy,
                sort_dir=body.sortDir,
                page=body.page,
                limit=body.limit,
            )

        return {"items": [result], "pagination": {"page": body.page, "limit": body.limit, "total": 1, "pages": 1}}
    except SolaryumError as error:
        try:
            _record_error(db, "MontarKits", error.message, error.details)
        except Exception:
            logger.exception("Erro ao registrar SolaryumError")
        raise _handle_solaryum_error(error)
    except Exception as exc:
        logger.error("Erro inesperado em MontarKits POST: %s", str(exc))
        try:
            _record_error(db, "MontarKits", str(exc), None)
        except Exception:
            logger.exception("Erro ao registrar exceção inesperada")
        raise HTTPException(
            status_code=500,
            detail={"error": "Erro interno", "message": "Ocorreu um erro ao processar sua requisição"},
        )