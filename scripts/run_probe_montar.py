#!/usr/bin/env python3
import json
from app.services.solaryum_service import montar_kits

payload = {
    'ibge': '2800308',
    'potencia_do_kit': 330.0,
    'potencia_do_painel': 330.0,
    'marca_painel': 17,
    'marca_inversor': 15,
    'telhados': [1],
}
print('Payload:', json.dumps(payload))
try:
    res = montar_kits(**payload)
    print('SUCCESS', type(res))
    # Print a short representation of the response
    if isinstance(res, (list, dict)):
        print(json.dumps(res, default=str)[:2000])
    else:
        print(repr(res))
except Exception as e:
    print('ERROR', type(e), str(e))
