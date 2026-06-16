import urllib.parse
from playwright.sync_api import sync_playwright

q = "Vem Passear em Jampa"
url = f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}&hl=pt-BR"

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    ctx = b.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        locale="pt-BR",
    )
    page = ctx.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(3000)

    title = page.title()
    h3s = page.evaluate("() => Array.from(document.querySelectorAll('h3')).map(h => h.innerText).slice(0,8)")
    body = page.evaluate("() => document.body.innerText.slice(0, 800)")
    b.close()

print("TITLE:", title)
print("H3s:", h3s)
print("BODY:\n", body)
