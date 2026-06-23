#!/usr/bin/env python3
"""
Trackea progreso vs benchmark MAE 7.2
"""
import pandas as pd
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

url = "https://qlbczflygozfvwyilhes.supabase.co/rest/v1/benchmark_logs?select=*&order=fecha.desc"
headers = {"apikey": os.getenv("SUPABASE_KEY")}

try:
    r = requests.get(url, headers=headers)
    logs = pd.DataFrame(r.json())

    print("📈 HISTÓRICO vs BENCHMARK (MAE 7.2)")
    print("=" * 50)

    for _, row in logs.head(10).iterrows():
        fecha = row['fecha'][:10]
        mae = row['mae_actual']
        mejora = row['mejora_porcentaje']
        status = "✅" if row['supera_benchmark'] else "🔧"

        print(f"{status} {fecha}: MAE={mae:.1f} ({mejora:+.1f}%)")

    print("=" * 50)

except:
    print("💡 Ejecuta primero tu modelo para generar logs")
