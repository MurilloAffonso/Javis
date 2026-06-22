"""Smoke test LIVE do OpenRouter — bloqueado por padrão.

Nunca imprime chave ou prefixo. Só permite rede com duas confirmações explícitas:
JAVIS_ALLOW_LIVE_OPENROUTER_TEST=1 e orçamento entre US$ 0,01 e US$ 0,10.
Os testes automatizados não habilitam essas flags.
"""
import os
import sys
from pathlib import Path

LIVE_FLAG = "JAVIS_ALLOW_LIVE_OPENROUTER_TEST"
BUDGET_ENV = "JAVIS_OPENROUTER_BENCHMARK_MAX_USD"
MODELS = (
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
)


def _approved_budget() -> float | None:
    try:
        budget = float(os.environ.get(BUDGET_ENV, "0"))
    except ValueError:
        return None
    return budget if 0.01 <= budget <= 0.10 else None


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if os.environ.get(LIVE_FLAG) != "1":
        print(f"BLOQUEADO: teste live desativado; defina {LIVE_FLAG}=1 somente com aprovação.")
        return 2

    budget = _approved_budget()
    if budget is None:
        print(f"BLOQUEADO: defina {BUDGET_ENV} entre 0.01 e 0.10.")
        return 2

    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[4] / ".env")
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    print("Chave configurada:", "sim" if key else "não")
    if not key:
        return 2

    from openai import OpenAI
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
        default_headers={"HTTP-Referer": "http://localhost:8000"},
    )

    for model in MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Responda só: Olá senhor."}],
                max_tokens=30,
                timeout=20,
            )
            print("MODELO RESOLVIDO:", response.model)
            print("RESPOSTA:", response.choices[0].message.content)
        except Exception as exc:
            print(f"ERRO {model}: {type(exc).__name__}")
    return 0


if __name__ == "__main__":
    main()
