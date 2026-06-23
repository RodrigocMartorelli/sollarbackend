from app.services.solaryum_service import montar_kits, buscar_filtros
import json, traceback

def test():
    filtros = buscar_filtros()
    if not filtros:
        print("Could not fetch filters")
        return

    # In a previous successful run (from terminal history):
    # Panel: Astronergy (71), Power: 450, Inverter: AuxSol (120), Roof: Ceramico (0)
    # worked for somebody? Wait, the history shows exit code 0 but no "SUCCESS" text in the last few lines.
    # Let's inspect what's available.
    
    print("Available Marcas Paineis (first 5):", filtros.get('marcasPaineis', [])[:5])
    print("Available Marcas Inversores (first 5):", filtros.get('marcasInversores', [])[:5])
    print("Available Tipos Telhados (first 5):", filtros.get('tiposTelhados', [])[:5])
    print("Available Potencias Paineis (first 5):", filtros.get('potenciasPaineis', [])[:5])

    # Let's try to find a valid combination by using IDs that actually exist in the filter response.
    try:
        brand_p = filtros['marcasPaineis'][0]['id']
        brand_i = filtros['marcasInversores'][0]['id']
        roof = [filtros['tiposTelhados'][0]['id']]
        # Find a non-zero power
        pot = 0
        for p in filtros['potenciasPaineis']:
            if p['potencia'] > 0:
                pot = float(p['potencia'])
                break
        
        print(f"\nTrying combination: pot={pot}, brand_p={brand_p}, brand_i={brand_i}, roof={roof}")
        
        res = montar_kits(
            potencia_do_kit=pot,
            potencia_do_painel=pot,
            marca_painel=brand_p,
            marca_inversor=brand_i,
            telhados=roof,
            ibge='2800308'
        )
        print('montar_kits returned type:', type(res))
        if isinstance(res, list):
            print('Result length:', len(res))
            if len(res) > 0:
                print('First result:', json.dumps(res[0], ensure_ascii=False))
    except Exception:
        traceback.print_exc()

test()
