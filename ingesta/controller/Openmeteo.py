import requests
import pandas as pd
from datetime import datetime, timedelta
import os, sys
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from prediccion.config import SUPABASE_URL, SUPABASE_KEY, COORDENADAS

# ── Constantes ────────────────────────────────────────────────────────────────
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEZONE = "America/Argentina/Buenos_Aires"
DIAS_HISTORICO = 90
BATCH_SIZE = 500  # Supabase acepta hasta 500 filas por POST


# ── Funciones ─────────────────────────────────────────────────────────────────
def obtener_temperatura_historica(
    zona: str, start_date: str, end_date: str
) -> Optional[pd.DataFrame]:
    """Consulta Open-Meteo y devuelve un DataFrame con fecha y temperatura media."""
    lat, lon = COORDENADAS[zona]
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_mean",
        "timezone": TIMEZONE,
    }
    try:
        r = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return pd.DataFrame({
            "fecha": data["daily"]["time"],
            "temperatura_media": data["daily"]["temperature_2m_mean"],
        })
    except requests.RequestException as e:
        print(f"  ⚠️  Error al consultar Open-Meteo para '{zona}': {e}")
        return None


def guardar_en_supabase(zona: str, df: pd.DataFrame) -> int:
    """
    Inserta registros en Supabase en lotes (bulk insert).
    Devuelve la cantidad de filas enviadas.
    """
    df = df.copy()
    df["zona"] = zona
    records = df[["fecha", "zona", "temperatura_media"]].to_dict(orient="records")

    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        r = requests.post(
            f"{SUPABASE_URL}/clima",
            headers=HEADERS,
            json=batch,          # ← un solo POST por lote en lugar de N posts
            timeout=15,
        )
        r.raise_for_status()
        total += len(batch)

    return total


def calcular_rango_fechas(dias: int = DIAS_HISTORICO) -> tuple[str, str]:
    hoy = datetime.now()
    return (
        (hoy - timedelta(days=dias)).strftime("%Y-%m-%d"),
        hoy.strftime("%Y-%m-%d"),
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    start, end = calcular_rango_fechas()
    print(f"🌡️  Obteniendo temperatura histórica ({DIAS_HISTORICO} días: {start} → {end})...")

    for zona in COORDENADAS:
        df = obtener_temperatura_historica(zona, start, end)

        if df is None or df.empty:
            print(f"  ⚠️  {zona}: sin datos")
            continue

        try:
            guardados = guardar_en_supabase(zona, df)
            print(f"  ✅  {zona}: {guardados} registros guardados")
        except requests.RequestException as e:
            print(f"  ❌  {zona}: error al guardar → {e}")

    print("✅ Temperatura actualizada en Supabase")


if __name__ == "__main__":
    main()
