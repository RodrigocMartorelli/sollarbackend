def calculate_pricing(
    kit_value,
    potencia_kwp,
    quantidade_inversores,
    quantidade_placas,
    consumo_kwh,
    tipo_funcionario,
):
    if potencia_kwp <= 10:
        inverter_installation = 250 + (160 * quantidade_inversores)
    else:
        inverter_installation = 450 + (160 * quantidade_inversores)

    if quantidade_placas <= 10:
        panel_installation = quantidade_placas * 100
    else:
        panel_installation = (10 * 100) + ((quantidade_placas - 10) * 85)

    if consumo_kwh <= 2000:
        material = 1500
    elif consumo_kwh <= 5000:
        material = 2000
    else:
        material = 2500

    maintenance = 300

    subtotal = (
        kit_value
        + inverter_installation
        + panel_installation
        + material
        + maintenance
    )

    imposto = subtotal * 0.05

    valor_com_imposto = subtotal + imposto

    employee_percent = (
        0.23 if tipo_funcionario.upper() == "CLT" else 0.30
    )

    employee_value = valor_com_imposto * employee_percent

    final_value = valor_com_imposto + employee_value

    return {
        "kitValue": round(kit_value, 2),
        "instalacaoInversor": round(inverter_installation, 2),
        "instalacaoPlacas": round(panel_installation, 2),
        "material": round(material, 2),
        "manutencao": round(maintenance, 2),
        "subtotal": round(subtotal, 2),
        "imposto": round(imposto, 2),
        "valorComImposto": round(valor_com_imposto, 2),
        "valorFuncionario": round(employee_value, 2),
        "valorFinalVenda": round(final_value, 2),
    }