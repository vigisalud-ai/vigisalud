import requests, pandas as pd, numpy as np, os, sys, joblib
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from prediccion.config import SUPABASE_URL, SUPABASE_KEY, FERIADOS_NACIONALES

headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# Cargar datos
response = requests.get(SUPABASE_URL + "?select=*&order=fecha.asc", headers=headers)
df = pd.DataFrame(response.json())
df['fecha'] = pd.to_datetime(df['fecha'])
df = df[df['fecha'] >= '2023-01-01'].copy()

# Feature engineering
fecha_min = df['fecha'].min()
df['dia_desde_inicio'] = (df['fecha'] - fecha_min).dt.days
df['mes'] = df['fecha'].dt.month
df['dia_semana'] = df['fecha'].dt.weekday
df['es_fin_de_semana'] = (df['dia_semana'] >= 5).astype(int)
df['es_feriado'] = df['fecha'].dt.strftime('%Y-%m-%d').isin(FERIADOS_NACIONALES).astype(int)
df['es_vacaciones'] = df['fecha'].apply(lambda f: 1 if f.month in [1,2,7] or (f.month==12 and f.day>=15) else 0)
df['finde_largo'] = 0

for lag in [1, 7, 14]:
    df[f'consultas_lag_{lag}'] = df.groupby('zona')['consultas'].shift(lag)
df['consultas_ma7'] = df.groupby('zona')['consultas'].transform(lambda x: x.rolling(7, min_periods=3).mean())
df = df.bfill()

# Features
num_features = ['dia_desde_inicio', 'mes', 'dia_semana', 'consultas_lag_1', 'consultas_lag_7',
                'consultas_lag_14', 'consultas_ma7', 'es_fin_de_semana', 'es_feriado',
                'es_vacaciones', 'finde_largo']
cat_features = ['zona']

X = df[num_features + cat_features]
y = df['consultas'].values

# Pipeline robusto
pipeline_model = Pipeline(steps=[
    ('preprocessor', ColumnTransformer(transformers=[
        ('num', SimpleImputer(strategy='median'), num_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)
    ])),
    ('regressor', RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_leaf=2, random_state=42, n_jobs=1))
])

# Validación
tscv = TimeSeriesSplit(n_splits=4)
maes = [mean_absolute_error(y[val], pipeline_model.fit(X.iloc[train], y[train]).predict(X.iloc[val]))
        for train, val in tscv.split(X)]
print(f"📈 MAE Validación: {np.mean(maes):.1f}")

# Entrenar y guardar
pipeline_model.fit(X, y)
joblib.dump(pipeline_model, 'modelo_v3_5.joblib')
print("✅ Pipeline entrenado y guardado como modelo_v3_5.joblib")
