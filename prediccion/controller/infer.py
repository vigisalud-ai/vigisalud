import requests, pandas as pd, numpy as np, os, sys, joblib
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from prediccion.config import SUPABASE_URL, SUPABASE_KEY, FERIADOS_NACIONALES
from alertas.controller.alertas_telegram import enviar_alerta

headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}

# 1. Cargar modelo congelado
model = joblib.load('modelo_v3_5.joblib')
print("✅ Modelo cargado")

# 2. Cargar datos recientes
response = requests.get(SUPABASE_URL + "?select=*&order=fecha.asc", headers=headers)
df = pd.DataFrame(response.json())
df['fecha'] = pd.to_datetime(df['fecha'])
df = df[df['fecha'] >= '2023-01-01'].copy()

fecha_min = df['fecha'].min()
fecha_max = df['fecha'].max()
fechas_fut = [fecha_max + timedelta(days=i) for i in range(1, 8)]

features_num = ['dia_desde_inicio', 'mes', 'dia_semana', 'consultas_lag_1', 'consultas_lag_7',
                'consultas_lag_14', 'consultas_ma7', 'es_fin_de_semana', 'es_feriado',
                'es_vacaciones', 'finde_largo']

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
        predicciones.append({
            'fecha': fechas_fut[i].strftime('%Y-%m-%d'),
            'zona': zona,
            'consultas_predichas': int(round(pred[i]))
        })

# 3. Guardar en Supabase
url_pred = "https://qlbczflygozfvwyilhes.supabase.co/rest/v1/predicciones"
for p in predicciones:
    requests.post(url_pred, headers=headers, json=p)
    print(f"✅ {p['fecha']} | {p['zona']} → {p['consultas_predichas']}")

# 4. Alertas
print("\n📱 Enviando alertas...")
for p in predicciones:
    enviar_alerta(p['zona'], p['consultas_predichas'], dia=p['fecha'])

print(f"✅ {len(predicciones)} predicciones guardadas")
