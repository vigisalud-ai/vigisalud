import requests, pandas as pd, numpy as np, os, sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from prediccion.config import SUPABASE_KEY
from alertas.controller.alertas_telegram import enviar_alerta

headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# 1. Obtener métricas de los últimos 7 días
url_logs = "https://qlbczflygozfvwyilhes.supabase.co/rest/v1/logs_metricas?select=*&fecha_ejecucion=gte.2026-05-28&order=fecha_ejecucion.desc&limit=7"
logs = requests.get(url_logs, headers=headers).json()

if len(logs) >= 3:
    maes = [l['mae'] for l in logs if l['mae'] is not None]
    mae_promedio = np.mean(maes)
    baseline = 7.0
    drift = ((mae_promedio - baseline) / baseline) * 100

    print(f"📊 MAE promedio 7 días: {mae_promedio:.1f}")
    print(f"📈 Baseline: {baseline}")
    print(f"📉 Data Drift: {drift:.1f}%")

    if drift > 20:
        mensaje = (
            f"⚠️ *DATA DRIFT DETECTADO*\n"
            f"📊 MAE promedio semanal: {mae_promedio:.1f}\n"
            f"📈 Baseline: {baseline}\n"
            f"📉 Deriva: +{drift:.0f}%\n"
            f"🎯 _Recomendación: Reentrenar modelo manualmente._"
        )
        enviar_alerta("Sistema", 0, dia="Data Drift")
        # También podés enviar a Telegram directo
        print("🚨 Alerta de Data Drift enviada")
    else:
        print("✅ Modelo estable")
else:
    print("⚠️ Pocos datos para detectar drift")
