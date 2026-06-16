import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
headers = {"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}

resp = requests.post(
    "https://html.duckduckgo.com/html/",
    data={"q": "Vem Passear em Jampa", "kl": "br-pt"},
    headers=headers,
    timeout=12,
)
print("STATUS:", resp.status_code)

soup = BeautifulSoup(resp.text, "html.parser")

# Ver todas as classes disponíveis
all_classes = set()
for tag in soup.find_all(True):
    for c in (tag.get("class") or []):
        all_classes.add(c)
print("CLASSES:", sorted(all_classes)[:30])

# Ver primeiros links
links = soup.find_all("a", href=True)[:10]
for a in links:
    print("LINK:", a.get("class"), "|", a.get_text(strip=True)[:60], "|", a["href"][:80])
