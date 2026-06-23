from flask import Blueprint, request, jsonify

from fastapi import APIRouter

router = APIRouter()

@router.post("/calculate-pricing")
async def calculate_pricing_route(data: dict):
    return calculate_pricing(
        kit_value=data["kitValue"],
        potencia_kwp=data["potenciaKwp"],
        quantidade_inversores=data["quantidadeInversores"],
        quantidade_placas=data["quantidadePlacas"],
        consumo_kwh=data["consumoKwh"],
        tipo_funcionario=data["tipoFuncionario"],
    )

    return jsonify(result)