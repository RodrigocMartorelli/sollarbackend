from app.services.solaryum_service import montar_kits
import traceback

try:
    montar_kits(integrator_token='jjvMk6Rl', company_token='yq#q6h9y5y#tLL', potencia_do_kit=6, ibge='2800308')
except Exception as e:
    print('Exception type:', type(e))
    print('Exception repr:', repr(e))
    traceback.print_exc()
