from app.services.solaryum_service import montar_kits, buscar_filtros
import json, traceback

def test():
    filtros = buscar_filtros()
    if not filtros:
        return

    # From previous output:
    # Marcas Paineis: {'idMarca': 62, 'descricao': '.0'}, {'idMarca': 71, 'descricao': 'ASTRONERGY'}
    # Marcas Inversores: {'idMarca': 120, 'descricao': 'AUXSOL'}
    # Tipos Telhados: {'id': 0, 'descricao': 'Cerâmico'}
    # Potencias: {'potencia': 330}

    valid_paineis = [m['idMarca'] for m in filtros['marcasPaineis'] if m['descricao'] != '.0']
    valid_inversores = [m['idMarca'] for m in filtros['marcasInversores']]
    valid_telhados = [t['id'] for t in filtros['tiposTelhados']]
    valid_potencias = [p['potencia'] for p in filtros['potenciasPaineis'] if p['potencia'] > 0]

    if not (valid_paineis and valid_inversores and valid_telhados and valid_potencias):
        print("Missing valid data")
        return

    brand_p = valid_paineis[0]
    brand_i = valid_inversores[0]
    roof = [valid_telhados[0]]
    pot = float(valid_potencias[0])

    print(f"Testing with: pot={pot}, brand_p={brand_p}, brand_i={brand_i}, telhados={roof}")

    try:
        res = montar_kits(
            potencia_do_kit=pot,
            potencia_do_painel=pot,
            marca_painel=brand_p,
            marca_inversor=brand_i,
            telhados=roof,
            ibge='2800308'
        )
        print('SUCCESS' if res else 'EMPTY')
        print(f'Result (Type: {type(res)}): {json.dumps(res, ensure_ascii=False)[:500]}')
    except Exception:
        traceback.print_exc()

test()
