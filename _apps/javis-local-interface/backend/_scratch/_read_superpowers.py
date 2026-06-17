import sys
sys.stdout.reconfigure(encoding='utf-8')
import browser

# README do repositório via raw GitHub
urls = [
    "https://raw.githubusercontent.com/obra/superpowers/main/README.md",
    "https://github.com/obra/superpowers",
]

for url in urls:
    print(f"\n=== {url} ===")
    res = browser.read_page(url)
    print(res['message'][:3000])
    print("...")
