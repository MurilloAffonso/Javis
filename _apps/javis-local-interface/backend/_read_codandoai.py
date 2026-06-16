import sys
sys.stdout.reconfigure(encoding='utf-8')
from ddgs import DDGS

results = list(DDGS().text('codandoai.com JARVIS AI curso avaliação', max_results=8))
for r in results:
    print(f"\nTÍTULO: {r.get('title')}")
    print(f"URL: {r.get('href')}")
    print(f"TEXTO: {r.get('body','')[:300]}")
    print("---")
