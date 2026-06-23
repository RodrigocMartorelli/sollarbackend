from app.services.solaryum_service import montar_kits, buscar_filtros
import json, traceback

def test_all():
    filtros = buscar_filtros()
    if not filtros: return

    paineis = [m['idMarca'] for m in filtros['marcasPaineis'] if m['descricao'] != '.0'][:3]
    inversores = [m['idMarca'] for m in filtros['marcasInversores']][:3]
    telhados = [t['id'] for t in filtros['tiposTelhados']][:2]
    pots = [p['potencia'] for p in filtros['potenciasPaineis'] if p['potencia'] > 0][:3]

    print(f"Paineis: {paineis}")
    print(f"Inversores: {inversores}")
    print(f"Telhados: {telhados}")
    print(f"Pots: {pots}")

    for pot in pots:
        for p_id in paineis:
            for i_id in inversores:
                for t_id in telhados:
                    try:
                        res = montar_kits(
                            potencia_do_kit=float(pot),
                            potencia_do_painel=float(pot),
                            marca_painel=p_id,
                            marca_inversor=i_id,
                            telhados=[t_id],
                            ibge='2800308'
                        )
                        if res:
                            print(f"SUCCESS! Pot: {pot}, P: {p_id}, I: {i_id}, T: {t_id}")
                            print(f"Result count: {len(res)}")
                            return
                    except:
                        pass
    print("No valid combination found in sample.")

test_all()
