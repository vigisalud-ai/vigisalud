# coding: utf-8
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error
import os
from dotenv import load_dotenv


print("🚀 VigiSalud - Modelo Final v3.5 | 7 días + Logs MAE")

# ==================== CONFIG ====================
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SUPABASE_URL, SUPABASE_KEY, COORDENADAS, FERIADOS_NACIONALES, UMBRALES
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from alertas.controller.alertas_telegram import enviar_alerta

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

def es_vacaciones(fecha):
    mes = fecha.month
    dia = fecha.day
    if mes in [1, 2] or (mes == 12 and dia >= 15) or mes == 7:
        return 1
    return 0

# ==================== CLIMA ====================
def get_historical_weather(lat, lon, start_date, end_date):
    try:
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {"latitude": lat, "longitude": lon, "start_date": start_date, "end_date": end_date,
                  "daily": "temperature_2m_mean", "timezone": "America/Argentina/Buenos_Aires"}
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        return pd.DataFrame({
            'fecha': pd.to_datetime(data['daily']['time']),
            'temperatura_media': data['daily']['temperature_2m_mean']
        })
    except:
        return pd.DataFrame()

# ==================== CARGAR DATOS ====================
response = requests.get(SUPABASE_URL + "?select=*&order=fecha.asc", headers=headers)
df = pd.DataFrame(response.json())
df['fecha'] = pd.to_datetime(df['fecha'])
df = df[df['fecha'] >= '2023-01-01'].copy()

# 🔥 NUEVO: Cargar features demográficas de Argentina Hub
from feature_engineering import cargar_datos_demograficos, agregar_features_demograficas

try:
    features_demo = cargar_datos_demograficos()
    df = agregar_features_demograficas(df, features_demo)
    print(f"📊 Features demográficas cargadas: {list(features_demo.keys())}")
except Exception as e:
    print(f"⚠ No se pudieron cargar features demográficas: {e}")

print(f"📊 Datos: {len(df)} registros | {df['fecha'].min().date()} → {df['fecha'].max().date()}")

# ==================== FEATURE ENGINEERING ====================
df = df.sort_values(['zona', 'fecha']).reset_index(drop=True)

df['dia_desde_inicio'] = (df['fecha'] - df['fecha'].min()).dt.days
df['mes'] = df['fecha'].dt.month
df['dia_semana'] = df['fecha'].dt.weekday
df['es_fin_de_semana'] = (df['dia_semana'] >= 5).astype(int)
df['es_feriado'] = df['fecha'].dt.strftime('%Y-%m-%d').isin(FERIADOS_NACIONALES).astype(int)
df['es_vacaciones'] = df['fecha'].apply(es_vacaciones)
df['es_no_laboral'] = (df['es_fin_de_semana'] | df['es_feriado'] | df['es_vacaciones']).astype(int)

df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
df['dia_semana_sin'] = np.sin(2 * np.pi * df['dia_semana'] / 7)

# Fin de semana largo (viernes si el lunes es feriado, o lunes si el viernes fue feriado)
df['finde_largo'] = 0
for idx, row in df.iterrows():
    if row['dia_semana'] == 4:  # Viernes
        lunes = row['fecha'] + pd.Timedelta(days=3)
        if lunes.strftime('%Y-%m-%d') in FERIADOS_NACIONALES:
            df.at[idx, 'finde_largo'] = 1
    if row['dia_semana'] == 0:  # Lunes
        viernes = row['fecha'] - pd.Timedelta(days=3)
        if viernes.strftime('%Y-%m-%d') in FERIADOS_NACIONALES:
            df.at[idx, 'finde_largo'] = 1

for lag in [1, 7, 14]:
    df[f'consultas_lag_{lag}'] = df.groupby('zona')['consultas'].shift(lag)

df['consultas_ma7'] = df.groupby('zona')['consultas'].transform(lambda x: x.rolling(7, min_periods=3).mean())

## Temperatura

# Cargar temperatura desde Supabase
clima_url = "https://qlbczflygozfvwyilhes.supabase.co/rest/v1/clima?select=*"
clima_df = pd.DataFrame(requests.get(clima_url, headers=headers).json())
if not clima_df.empty:
    clima_df['fecha'] = pd.to_datetime(clima_df['fecha'])
    df = df.merge(clima_df, on=['fecha', 'zona'], how='left')
    df['temperatura_media'] = df['temperatura_media'].fillna(df['temperatura_media'].mean())

# ==================== MODELO ====================
# 🔥 NUEVO: 6 features demográficas agregadas al final
features_num = ['dia_desde_inicio', 'mes', 'dia_semana', 'mes_sin', 'dia_semana_sin',
                'consultas_lag_1', 'consultas_lag_7', 'consultas_lag_14', 'consultas_ma7',
                'es_fin_de_semana', 'es_feriado', 'es_vacaciones', 'es_no_laboral',
                'poblacion_total', 'pct_mujeres', 'pct_piso_tierra', 'pct_vivienda_precaria',
                'pct_sin_cobertura', 'poblacion_sin_cobertura']

X = df[features_num + ['zona']]
y = df['consultas'].values

modelo = Pipeline([
    ('preprocessor', ColumnTransformer([
        ('num', SimpleImputer(strategy='median'), features_num),
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['zona'])
    ])),
    ('model', RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_leaf=2, random_state=42, n_jobs=1))
])
modelo.fit(X, y)


y_pred = modelo.predict(X.iloc[-30:])
mae_bt = mean_absolute_error(y[-30:], y_pred)
r2_bt = r2_score(y[-30:], y_pred)
print(f"📉 MAE Backtesting: {mae_bt:.1f} consultas | R²: {r2_bt:.2%}\n")

# ==================== PREDICCIÓN 7 DÍAS ====================
print("🔮 Generando predicciones (próximos 7 días)...")

from datetime import date
fecha_max = pd.Timestamp(date.today())
fechas_fut = [fecha_max + timedelta(days=i) for i in range(1, 8)]

predicciones = []
for zona in ['Norte', 'Centro', 'Sur']:
    futuro = pd.DataFrame({'fecha': fechas_fut, 'zona': zona})
    
    futuro['dia_desde_inicio'] = (futuro['fecha'] - df['fecha'].min()).dt.days
    futuro['mes'] = futuro['fecha'].dt.month
    futuro['dia_semana'] = futuro['fecha'].dt.weekday
    futuro['es_fin_de_semana'] = (futuro['dia_semana'] >= 5).astype(int)
    futuro['es_feriado'] = futuro['fecha'].dt.strftime('%Y-%m-%d').isin(FERIADOS_NACIONALES).astype(int)
    futuro['es_vacaciones'] = futuro['fecha'].apply(es_vacaciones)
    futuro['es_no_laboral'] = (futuro['es_fin_de_semana'] | futuro['es_feriado'] | futuro['es_vacaciones']).astype(int)
    
    futuro['mes_sin'] = np.sin(2 * np.pi * futuro['mes'] / 12)
    futuro['dia_semana_sin'] = np.sin(2 * np.pi * futuro['dia_semana'] / 7)

    last = df[df['zona'] == zona].iloc[-1]
    for col in ['consultas_lag_1', 'consultas_lag_7', 'consultas_lag_14', 'consultas_ma7']:
        futuro[col] = last[col]
    futuro['temperatura_media'] = last.get('temperatura_media', 15.0)
    
    # 🔥 NUEVO: Features demográficas (constantes por zona)
    for col in ['poblacion_total', 'pct_mujeres', 'pct_piso_tierra', 'pct_vivienda_precaria',
                'pct_sin_cobertura', 'poblacion_sin_cobertura']:
        futuro[col] = last[col]

    pred = modelo.predict(futuro[features_num + ['zona']])
    
    for i in range(len(fechas_fut)):
        predicciones.append({
            'fecha': fechas_fut[i].strftime('%Y-%m-%d'),
            'zona': zona,
            'consultas_predichas': int(round(pred[i]))
        })

df_pred = pd.DataFrame(predicciones)
df_pred.to_csv('predicciones_7_dias.csv', index=False)
print(f"💾 CSV guardado: {len(df_pred)} registros")

# ==================== SUBIR PREDICCIONES ====================
print("\n📤 Subiendo predicciones...")

alertas_enviadas = 0

for _, row in df_pred.iterrows():
    data = {
        'fecha': row['fecha'],
        'zona': row['zona'],
        'consultas_predichas': row['consultas_predichas']
    }
    requests.post("https://qlbczflygozfvwyilhes.supabase.co/rest/v1/predicciones", headers=headers, json=data)
    print(f"✅ {row['fecha']} | {row['zona']:8} → {row['consultas_predichas']}")

# ==================== GUARDAR MAE ====================
print("\n📊 Guardando métrica...")
log_data = {
    'fecha_ejecucion': datetime.now().strftime('%Y-%m-%d'),
    'mae': float(mae_bt),
    'r2': float(r2_bt),
    'n_reg': len(df)
}

requests.post("https://qlbczflygozfvwyilhes.supabase.co/rest/v1/logs_metricas", headers=headers, json=log_data)
print(f"📈 MAE del día guardado: {mae_bt:.1f}")

# ==================== ALERTAS TELEGRAM ====================
print("\n📱 Enviando alertas...")

from datetime import date
hoy = date.today()

for _, row in df_pred.iterrows():
    if row['fecha'] >= str(hoy):
        enviar_alerta(row['zona'], row['consultas_predichas'], dia=row['fecha'])
        alertas_enviadas += 1

print(f"✅ {alertas_enviadas} alertas procesadas")

import joblib
joblib.dump(modelo, 'modelo_v3_5.joblib')
print("✅ Modelo guardado para inferencia")
print("\n🎉 ¡Proceso completado correctamente!")

# Exportar explicación como JSON para el dashboard
# Exportar explicación como JSON para el dashboard
import json

# Extraer importancia real de features
feature_names = modelo.named_steps['preprocessor'].get_feature_names_out()
importances = modelo.named_steps['model'].feature_importances_

explicacion = {
    "fecha": datetime.now().strftime("%Y-%m-%d"),
    "factores": {}
}

for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True):
    explicacion["factores"][name] = round(float(imp), 4)

with open("explicacion_prediccion.json", "w") as f:
    json.dump(explicacion, f, indent=2, ensure_ascii=False)

print("📊 Explicación exportada a explicacion_prediccion.json")

# Enviar factores a Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
if TELEGRAM_TOKEN and CHAT_ID:
    top3 = list(explicacion["factores"].items())[:3]
    msg = "🧠 *Factores que más influyen hoy:*\n"
    for nombre, peso in top3:
        msg += f"• {nombre}: {round(peso*100, 1)}%\n"
    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )
    print(f"📱 Respuesta Telegram: {resp.json()}")
else:
    print("⚠ No se encontró TELEGRAM_TOKEN o CHAT_ID en .env")
