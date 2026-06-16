import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv("../../../.env")

from openai import OpenAI

key = os.environ.get("OPENROUTER_API_KEY", "")
print("Chave:", key[:20], "...")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=key,
    default_headers={"HTTP-Referer": "http://localhost:8000"},
)

# Testa modelo gratuito pequeno
try:
    r = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct:free",
        messages=[{"role": "user", "content": "Responda só: Olá senhor."}],
        max_tokens=30,
        timeout=20,
    )
    print("RESPOSTA:", r.choices[0].message.content)
    print("MODELO:", r.model)
except Exception as e:
    print("ERRO llama-8b:", e)

# Testa modelo gratuito maior
try:
    r2 = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct:free",
        messages=[{"role": "user", "content": "Responda só: Olá senhor."}],
        max_tokens=30,
        timeout=20,
    )
    print("RESPOSTA mistral:", r2.choices[0].message.content)
except Exception as e:
    print("ERRO mistral:", e)
