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
