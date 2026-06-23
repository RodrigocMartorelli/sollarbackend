from app.services.solaryum_service import buscar_kits, montar_kits, buscar_filtros
import json, traceback
try:
    filters = buscar_filtros()
    print('Sample filter potencia items:', filters.get('potenciasPaineis',[])[:10])

    print('\nRunning buscar_kits with potencia_do_kit=330.0')
    try:
        res = buscar_kits(potencia_do_kit=330.0)
        print('buscar_kits returned:', type(res), len(res) if isinstance(res, list) else 'n/a')
        if isinstance(res, list):
            print('First items:', json.dumps(res[:3], ensure_ascii=False))
    except Exception:
        traceback.print_exc()

    print('\nRunning montar_kits with potencia_do_kit=330.0')
    try:
        res = montar_kits(potencia_do_kit=330.0, potencia_do_painel=330.0, marca_painel=71, marca_inversor=120, telhados=[0], ibge='2800308')
        print('montar_kits returned:', type(res), len(res) if isinstance(res, list) else 'n/a')
        if isinstance(res, list):
            print('First items:', json.dumps(res[:3], ensure_ascii=False))
    except Exception:
        traceback.print_exc()
except Exception:
    traceback.print_exc()
