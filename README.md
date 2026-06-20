![Python](https://img.shields.io/badge/Python-3.11-blue)




![MAE](https://img.shields.io/badge/MAE-4.0--preliminar-brightgreen)




![License](https://img.shields.io/badge/License-MIT-yellow)




![Status](https://img.shields.io/badge/Status-Production-success)



# 🏥 VigiSalud v3.5

**Predicción inteligente de picos de demanda en Guardias Médicas**

Desarrollado desde un **Moto G56 con Termux**.

---

## 🎯 Objetivo

Anticipar con **7-14 días de anticipación** el volumen de consultas en la Guardia Central (foco inicial en Traumatología y Ortopedia).

---

## ✨ Características Principales

- Predicción con **MAE = 4.0** consultas/día (preliminar — ver sección Resultados)
- **MAE esperado en producción**: 7-10 consultas/día
- Integración de variables climáticas y calendarias
- Validación temporal estricta (`TimeSeriesSplit`)
- Dashboard web + Alertas automáticas por Telegram
- Ejecución diaria con GitHub Actions
- ✅ **Ingesta desde datos reales de guardia** (OCR + RAG con Llama 3.2 + ChromaDB)

---

## 🏗️ Arquitectura (5 Capas)

| Capa                | Implementación                                                                | Impacto                                   |
|---------------------|--------------------------------------------------------------------------------|--------------------------------------------|
| **🔗 Conectividad**     | Supabase + Open-Meteo + World Bank                                           | Datos centralizados en tiempo real        |
| **🧠 Inteligencia**     | Random Forest Regressor + 14 features temporales + 6 demográficas (20 total) | MAE 4.0 (preliminar)                      |
| **⚡ Automatización**   | GitHub Actions (6 AM) + Limpieza cada 72h                                    | Ejecución automática                      |
| **📊 Experiencia**      | Chart.js Dashboard + Bot de Telegram                                         | Fácil de usar desde cualquier dispositivo |
| **🛡️ Gobernanza**       | RLS + Cifrado + Licencia MIT                                                 | Seguridad y código abierto                |

---

## 📊 Resultados

- **MAE actual**: 4.0 consultas/día (preliminar, datos mixtos)
- **MAE esperado en producción**: 7-10 consultas/día

> ⚠️ **Nota:** El MAE de 4.0 es preliminar, obtenido con datos mixtos (simulados + reales). El piloto de 30 días en Las Lomitas determinará el MAE real en producción, estimado entre 7-10 consultas/día.

---

## 🛠️ Tecnologías

- 🐍 **Python 3.11** + scikit-learn + pandas
- 🐘 **Supabase** (PostgreSQL + RLS)
- 🌡️ **Open-Meteo API**
- 📊 **Chart.js** + GitHub Pages
- 🔄 **GitHub Actions**
- 🤖 **NVIDIA Llama 3.3** (para partes clínicas)
- 📱 **Termux** (Moto G56)

---

## 🔒 Seguridad y Cumplimiento

- **RLS**: Row Level Security en todas las tablas
- **Datos**: Solo métricas agregadas (sin información de pacientes)
- **Cifrado**: SSL/TLS + AES-256 (Supabase)
- **Cumplimiento**: Compatible con Ley de Protección de Datos Personales

---

## 🔗 Interoperabilidad

- **Estándar futuro**: HL7/FHIR (próxima fase)
- **Conexión**: API REST + CSV
- **Compatibilidad**: Sistemas de historia clínica electrónica

---

## 🚀 Instalación y Uso

\`\`\`bash
git clone https://github.com/vigisalud-ai/vigisalud.git
cd vigisalud
pip install -r requirements.txt
\`\`\`

Configuración (archivo `.env`):

\`\`\`
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_key
TELEGRAM_TOKEN=tu_telegram_bot_token
TELEGRAM_CHAT_ID=tu_chat_id
NVIDIA_API_KEY=tu_key (opcional)
\`\`\`

Comandos principales:

\`\`\`bash
python prediccion/controller/modelo_v3_5.py       # Pipeline completo
python prediccion/controller/train.py             # Entrenar modelo
python prediccion/controller/infer.py             # Inferencia
python prediccion/controller/consulta_clinica.py  # Consulta a Llama 3.3
\`\`\`

---

## 🧭 Filosofía del Proyecto

| Principio | Por qué importa |
|-----------|-----------------|
| 🩺 **Doble validación** | Responde a una necesidad clínica real |
| 📱 **Sin compu no es excusa** | Termux + GitHub Actions = producción |
| 💰 **Costo cero** | Stack 100% gratuito |
| 🧠 **KISS** | Arquitectura modular |

---

## 🌐 Demo en Vivo

👉 [Ver Dashboard](https://vigisalud-ai.github.io/Vigisalud-dashboard/)

---

## 💻 Arquitectura de ejecución

VigiSalud usa datos demográficos reales de **[Argentina Hub](https://github.com/hectory2k/argentina-hub)**, un proyecto complementario que cura datasets públicos argentinos (Censo 2022, INDEC, BCRA).

VigiSalud corre en dos dispositivos con tareas divididas:

| Dispositivo | Tarea | Fundamento |
|-------------|-------|------------|
| **Manjaro (i5)** | `censo_extractor.py` → staging/ | `duckdb` wheel Linux x86_64 |
| **Moto G56 (Termux)** | build, DPA, Indicadores, Modelo_v3_5 | Sin dependencia de duckdb |

### Features demográficas sin duckdb

`feature_engineering.py` en Termux carga `features_patino.json` (precalculado en Manjaro con `censoargentino`).

### Flujo diario

\`\`\`
Manjaro: extract censo → git push
Moto:    git pull → build → modelo_v3_5.py → predicciones → Telegram
\`\`\`

---

## 📝 Licencia

MIT License - Uso libre para fines educativos, de investigación y salud pública.
Para uso comercial o implementación institucional, contactar al autor.
