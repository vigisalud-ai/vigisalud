import requests
from datetime import datetime, timedelta
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from prediccion.config import SUPABASE_KEY

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

base_url = "https://qlbczflygozfvwyilhes.supabase.co/rest/v1"

# Borrar predicciones de más de 14 días
limite = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
r = requests.delete(f"{base_url}/predicciones?fecha=lt.{limite}", headers=headers)
print(f"🧹 Predicciones antiguas eliminadas: {r.status_code}")

# Borrar consultas históricas de más de 90 días
limite_consultas = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
r = requests.delete(f"{base_url}/consultas_historicas?fecha=lt.{limite_consultas}", headers=headers)
print(f"🧹 Consultas antiguas eliminadas: {r.status_code}")

print("✅ Limpieza completada")
