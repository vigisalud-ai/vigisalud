![Python](https://img.shields.io/badge/Python-3.11-blue) ![MAE](https://img.shields.io/badge/MAE-7.0-brightgreen) ![License](https://img.shields.io/badge/License-MIT-yellow) ![Built](https://img.shields.io/badge/Built-Moto_G65-orange) ![Status](https://img.shields.io/badge/Status-Production-success) ![NVIDIA](https://img.shields.io/badge/NVIDIA-Llama_3.3-76B900?logo=nvidia)

# 🏥 VigiSalud v3.5

Predicción de picos de consultas ortopédicas con datos abiertos, lag features y modelos estacionales.  
Desarrollado como proyecto para **Humai** desde un Moto G56 (Termux).

## 🎯 Objetivo
Anticipar picos de consultas por zona con 1-2 semanas de anticipación para priorizar operativos y recursos en traumatología.

## 🌐 Ecosistema de Salud Inteligente (5 Capas de Globant)

> *"La transición hacia una inteligencia predictiva ya no es una opción de laboratorio; es la infraestructura que los sistemas de salud necesitan con urgencia para subsistir."*  
> — Globant, *The Next Frontier of Healthcare Transformation*, 2026

| Capa Globant | Implementación VigiSalud | Impacto Operativo |
| :--- | :--- | :--- |
| **🔗 Conectividad** | Supabase + Open-Meteo + World Bank | Centralización de datos abiertos y variables climáticas |
| **🧠 Inteligencia** | Random Forest (MAE: 7.0) + 14 Lag & Temporal Features | Predicción de picos con 1-2 semanas de anticipación |
| **⚡ Automatización** | GitHub Actions (6 AM) + Limpieza (72h) | Inferencia diaria sin servidores propios |
| **📊 Experiencia** | Dashboard Chart.js + Alertas Telegram | Visualización ágil y notificaciones al equipo |
| **🛡️ Gobernanza** | RLS + Cifrado + Licencia MIT | Control de acceso y transparencia Open Source |

## ⚙️ Arquitectura del Pipeline y Modelado

El core predictivo está diseñado bajo estrictos criterios de validación cronológica y eficiencia computacional para entornos móviles.
[Inferencia] ──────────────► Random Forest Regressor ──► Despliegue en JSON (Dashboard)
```
### 🧠 Componentes Clave

- **Algoritmo:** Random Forest Regressor (Optimizado para relaciones no lineales exógenas)
- **Estrategia Anti-Leakage:** Validación temporal estricta (TimeSeriesSplit) para evitar contaminación de información futura
- **Robustez Exógena:** Integración de factores climáticos (Open-Meteo) y dinámicas de movilidad urbana (fines de semana largos y feriados)

### 🔧 Contingencias

| Riesgo | Estrategia |
|--------|------------|
| **API Open-Meteo caída** | `SimpleImputer` rellena `temperatura_media` con la mediana histórica |
| **Datos faltantes** | `SimpleImputer(strategy='median')` en features numéricas |
| **Nuevas categorías** | `OneHotEncoder(handle_unknown='ignore')` |

## 📊 Resultados

| Métrica | v2.1 | v3.5 | Mejora |
|---------|------|------|--------|
| **MAE** | 41.3 | **7.0** | -83% |
| **Backtesting (30 días)** | 13.4 | 7.0 | -48% |
| **Features** | 13 | 14 + `finde_largo` | +1 |
| **Registros** | 378 | 378 | - |

## 🔄 Arquitectura General

```mermaid
flowchart TD
    A[📊 Fuentes de Datos] --> B[🐍 Scripts de Ingesta]
    B --> C[🐘 Supabase PostgreSQL]
    C --> D[🧠 Modelo Predictivo]
    D --> E[📈 Predicciones]
    E --> F[📊 Dashboard]
    
    subgraph Fuentes
        A1[🌐 World Bank API]
        A2[🌡️ Open-Meteo API]
    end
    
    subgraph Ingesta
        B1[datos_reales.py]
        B2[datos_extra.py]
        B3[openmeteo.py]
    end
    
    subgraph Modelos
        D1[modelo_v3_5.py]
        D2[GitHub Actions - 6 AM]
    end
    
    subgraph Dashboard
        F1[Supabase Charts]
        F2[Chart.js + GitHub Pages]
    end
    
    A1 --> B1
    A2 --> B3
    B1 --> C
    B2 --> C
    B3 --> C
    C --> D1
    D1 --> D2
    D1 --> E
    E --> F1
    E --> F2


## ⏰ Orquestación Diaria

```mermaid
graph LR
    subgraph Orquestacion [GitHub Actions]
        Cron[⏰ 6 AM] -->|Dispara| Runner[Runner Virtual]
        Runner -->|Ejecuta| Script[modelo_v3_5.py]
    end
    subgraph Pipeline
        Script -->|Consulta| DB[(Supabase)]
        Script -->|Entrena| RF[Random Forest]
        RF -->|Calcula| Eval[MAE / RMSE]
    end
    subgraph Resultados
        Eval -->|Guarda| Log[(logs_metricas)]
    end
    style Cron fill:#24292e,color:#fff
    style Runner fill:#2dba4e,color:#fff
    style Log fill:#ff4757,color:#fff


## 🌐 Dashboard en vivo
👉 [Ver dashboard público](https://vigisalud-ai.github.io/Vigisalud-dashboard/)

## 🛠️ Tecnologías
- 🐍 Python 3.11 + scikit-learn + pandas
- 🐘 Supabase (PostgreSQL + RLS)
- 📱 Termux (Moto G56)
- ☁️ Azure App Service
- 📊 Chart.js + GitHub Pages
- 🤖 NVIDIA Llama 3.3 (partes clínicos)

## 🕐 Huso Horario
Todos los datos se almacenan en **UTC**.

## 🔒 Seguridad y Cumplimiento
- **Cifrado:** SSL/TLS + AES-256 (Supabase)
- **Anonimización:** Seudonimización antes de APIs externas
- **RLS:** Row Level Security en todas las tablas

## 🔗 Interoperabilidad
- **Estándar:** HL7/FHIR (próxima fase)
- **Conexión:** API REST + CSV

## 🧭 Filosofía del proyecto

| Principio | Por qué importa |
|-----------|-----------------|
| 🩺 **Doble validación** | Responde a una necesidad clínica real |
| 📱 **Sin compu no es excusa** | Termux + GitHub Actions = producción |
| 💰 **Costo cero** | Stack 100% gratuito |
| 🧠 **KISS** | Arquitectura modular |

## 👤 Autor
Hector | [GitHub](https://github.com/vigisalud-ai)

## 📝 Licencia
MIT
