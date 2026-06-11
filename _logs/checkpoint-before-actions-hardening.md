# Checkpoint — Antes do Hardening do actions.py

**Data/hora:** 2026-06-11 03:45 (horário local)
**Responsável:** Claude Code — Auditor de Segurança de Ações Locais
**Fase:** Correção de bugs de segurança em actions.py antes da primeira execução real por voz

---

## Objetivo

Corrigir três bugs concretos em `_apps/javis-local-interface/backend/actions.py`:

1. `_open_vscode` usa `subprocess.Popen(["code", path], shell=True)` — combinação insegura no Windows
2. `_open_terminal` usa f-string com path dentro do comando PowerShell — pode quebrar com aspas
3. `_register_idea` não valida texto vazio nem limita tamanho

---

## git status --short (subtree javis/) antes da mudança

```
?? ./
```

(Toda a pasta `javis/` ainda sem commits — repositório git root em `C:\Users\noteacer`)

---

## Bugs identificados

### Bug 1 — `_open_vscode` (linha 77)
```python
# ANTES — inseguro
subprocess.Popen(["code", path], shell=True)
```
- `shell=True` com lista no Windows → cmd.exe envolve o comando, comportamento imprevisível
- Não verifica se VS Code está instalado
- Não verifica se o diretório existe

### Bug 2 — `_open_terminal` (linha 83)
```python
# ANTES — inseguro
subprocess.Popen(["powershell.exe", "-NoExit", "-Command",
                  f"cd '{JAVIS_ROOT}'"])
```
- f-string interpola path dentro de string de comando PowerShell
- Aspas simples no path quebrariam a instrução `-Command`
- Exemplo de falha: `cd 'C:\Murillo's Desktop\javis'` → erro de sintaxe PowerShell

### Bug 3 — `_register_idea` (linhas 91–98)
```python
# ANTES — sem validação
def _register_idea(text: str) -> dict:
    ideas_dir = JAVIS_ROOT / "_ideias"
    ideas_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    file = ideas_dir / f"ideia_{stamp}.md"
    content = f"# Ideia — {stamp}\n\n{text}\n"
    file.write_text(content, encoding="utf-8")
```
- Texto vazio → cria arquivo vazio (ruído)
- Texto muito longo → sem limite de tamanho

---

## Confirmações obrigatórias

- ✅ `dry_run=True` continuará hardcoded em `voice_bridge.py` — NÃO será alterado
- ✅ Nenhuma execução real por voz será liberada por esta operação
- ✅ Apenas `actions.py` e `tests/test_actions.py` serão modificados
- ✅ Nenhum arquivo será apagado
- ✅ Nenhum `git add` / `git commit` / `git push` será executado
- ✅ Open WebUI e Docker não serão tocados
- ✅ Nada será instalado
