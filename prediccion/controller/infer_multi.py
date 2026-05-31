import requests, pandas as pd, numpy as np, os, sys, joblib
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from prediccion.config import SUPABASE_KEY, FERIADOS_NACIONALES

headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def enviar_telegram(chat_id, mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"})

def despachar_alertas_diarias():
    # 1. Traer instituciones activas
    url_inst = "https://qlbczflygozfvwyilhes.supabase.co/rest/v1/instituciones?estado_suscripcion=eq.activo"
    instituciones = requests.get(url_inst, headers=headers).json()
    print(f"🏥 {len(instituciones)} instituciones activas")

    # 2. Cargar modelo
    model = joblib.load('modelo_v3_5.joblib')
    print("✅ Modelo cargado")

    url_consultas = "https://qlbczflygozfvwyilhes.supabase.co/rest/v1/consultas_historicas?select=*&order=fecha.asc"
    response = requests.get(url_consultas, headers=headers)
    df = pd.DataFrame(response.json())
    df['fecha'] = pd.to_datetime(df['fecha'])
    df = df[df['fecha'] >= '2023-01-01'].copy()

    fecha_min = df['fecha'].min()
    fecha_max = df['fecha'].max()
    fechas_fut = [fecha_max + timedelta(days=i) for i in range(1, 8)]

    features_num = ['dia_desde_inicio', 'mes', 'dia_semana', 'consultas_lag_1', 'consultas_lag_7',
                    'consultas_lag_14', 'consultas_ma7', 'es_fin_de_semana', 'es_feriado',
                    'es_vacaciones', 'finde_largo']

    for inst in instituciones:
        id_cliente = inst['id']
        nombre = inst['nombre']
        chat_id = inst.get('telegram_chat_id')

        predicciones = []

        for zona in ['Norte', 'Centro', 'Sur']:
            futuro = pd.DataFrame({'fecha': fechas_fut, 'zona': zona})
            futuro['dia_desde_inicio'] = (futuro['fecha'] - fecha_min).dt.days
            futuro['mes'] = futuro['fecha'].dt.month
            futuro['dia_semana'] = futuro['fecha'].dt.weekday
            futuro['es_fin_de_semana'] = (futuro['dia_semana'] >= 5).astype(int)
            futuro['es_feriado'] = futuro['fecha'].dt.strftime('%Y-%m-%d').isin(FERIADOS_NACIONALES).astype(int)
            futuro['es_vacaciones'] = futuro['fecha'].apply(lambda f: 1 if f.month in [1,2,7] or (f.month==12 and f.day>=15) else 0)
            futuro['finde_largo'] = 0

            last = df[df['zona'] == zona].iloc[-1]
            for col in ['consultas_lag_1', 'consultas_lag_7', 'consultas_lag_14', 'consultas_ma7']:
                futuro[col] = last[col] if col in last.index else df['consultas'].mean()

            pred = model.predict(futuro[features_num + ['zona']])

            for i in range(len(fechas_fut)):
                valor = int(round(pred[i]))
                predicciones.append({
                    'fecha': fechas_fut[i].strftime('%Y-%m-%d'),
                    'zona': zona,
                    'consultas_predichas': valor,
                    'institucion_id': id_cliente
                })

                # 3. Alerta si supera umbral
                umbral = 130 if zona == 'Norte' else 110 if zona == 'Centro' else 90
                if valor > umbral and chat_id:
                    mensaje = (
                        f"🚨 *ALERTA VIGISALUD - {nombre.upper()}*\n"
                        f"📈 Pico proyectado en *Zona {zona}*.\n"
                        f"🔮 Predicción: {valor} consultas (±7).\n"
                        f"📅 Fecha: {fechas_fut[i].strftime('%Y-%m-%d')}.\n"
                        f"🎯 _Recomendación: Reforzar guardia y validar stock de insumos._"
                    )
                    enviar_telegram(chat_id, mensaje)

        # Guardar en Supabase
        url_pred = "https://qlbczflygozfvwyilhes.supabase.co/rest/v1/predicciones"
        for p in predicciones:
            requests.post(url_pred, headers=headers, json=p)

        print(f"✅ {nombre}: {len(predicciones)} predicciones")

    print("🎉 Despacho multi-cliente completado")

if __name__ == "__main__":
    despachar_alertas_diarias()
