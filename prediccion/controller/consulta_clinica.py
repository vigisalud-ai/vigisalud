import requests, os, sys
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from prediccion.config import SUPABASE_KEY

client = OpenAI(
    base_url='https://integrate.api.nvidia.com/v1',
    api_key=os.getenv('NVIDIA_API_KEY')
)

# Obtener predicciones del día para contexto
url = "https://qlbczflygozfvwyilhes.supabase.co/rest/v1/predicciones?select=*&order=fecha.asc&limit=21"
headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
predicciones = requests.get(url, headers=headers).json()

contexto = "Predicciones VigiSalud para los próximos días:\n"
for p in predicciones:
    contexto += f"- {p['fecha']} | {p['zona']}: {p['consultas_predichas']} consultas\n"

# Pregunta del médico
pregunta = input("🩺 Consulta clínica: ")

prompt = f"""{contexto}

Un médico traumatólogo pregunta:
{pregunta}

Respondé como un asistente médico especializado en ortopedia y traumatología. Sé concreto, basado en evidencia, y mencioná los datos de VigiSalud si son relevantes. NO analices economía, turismo, ni tendencias regionales no médicas. Respondé SOLO sobre el caso clínico."""

print("\n🦙 Llama 3.3 responde:\n")
completion = client.chat.completions.create(
    model='meta/llama-3.3-70b-instruct',
    messages=[{'role':'user','content':prompt}],
    temperature=0.6,
    max_tokens=800,
    stream=False
)

print(completion.choices[0].message.content)
