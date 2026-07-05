# Delegação Automática Claude→Codex — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar delegação automática de tarefas de execução do Claude pro Codex, economizando cota do cérebro (raciocínio fica no Claude, execução vai pro Codex).

**Architecture:** Atalho determinístico por verbo (`delegacao.py`: should_delegate) rota tarefas óbvias de execução direto pro Codex sem classificação LLM. Tarefas ambíguas caem numa rota `exec` no orchestrator que classifica leve. Reusa `brain_switch.dispatch` + `_audit_after_codex` existentes. Política documentada numa skill (`delegar-execucao.md`) pra Murillo editar. Preâmbulo de guarda no brief inibe commit/push.

**Tech Stack:** Python 3.14, pytest (mocks, nenhuma chamada real de LLM), re (regex), `brain_switch`, `code_agent`, `orchestrator`.

---

## File Structure

```
backend/
  delegacao.py                    [CREATE] — política (should_delegate, montar_brief)
  orchestrator.py                 [MODIFY] — +rota _run_exec (linhas ~110-130)
  brain_switch.py                 [MODIFY] — +engine param em dispatch (linha ~53)

_skills/
  delegar-execucao.md             [CREATE] — documentação da política pra Murillo

tests/
  test_delegacao.py               [CREATE] — testes de should_delegate + montar_brief
  test_orchestrator_exec.py       [CREATE] — testes da rota exec no orchestrator
```

---

## Task 1: `delegacao.py` — should_delegate() com testes

**Files:**
- Create: `backend/delegacao.py`
- Create: `tests/test_delegacao.py`

- [ ] **Step 1: Write failing test para should_delegate()**

`tests/test_delegacao.py`:
```python
import pytest
from backend.delegacao import should_delegate

def test_should_delegate_programa():
    """Verbo 'programa' é execução."""
    assert should_delegate("programa uma função que faz X") is True

def test_should_delegate_implementa():
    """Verbo 'implementa' é execução."""
    assert should_delegate("implementa o algoritmo de sort") is True

def test_should_delegate_refatora():
    """Verbo 'refatora' é execução."""
    assert should_delegate("refatora o arquivo X") is True

def test_should_delegate_roda():
    """Verbo 'roda' é execução."""
    assert should_delegate("roda os testes do projeto") is True

def test_should_delegate_cria_arquivo():
    """Verbo 'cria' com arquivo é execução."""
    assert should_delegate("cria o arquivo main.py") is True

def test_should_delegate_corrige_bug():
    """Verbo 'corrige' é execução."""
    assert should_delegate("corrige o bug na linha 42") is True

def test_should_delegate_normal_pergunta():
    """Pergunta normal não delega."""
    assert should_delegate("qual é a capital do Brasil?") is False

def test_should_delegate_raciocinio():
    """Tarefa de raciocínio não delega."""
    assert should_delegate("analisa este código e explica o que faz") is False

def test_should_delegate_planning():
    """Planejamento não delega."""
    assert should_delegate("monta um plano pra refatorar o projeto") is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd C:\Users\noteacer\Desktop\javis\_apps\javis-local-interface
python -m pytest tests/test_delegacao.py -v
```

Expected output:
```
FAILED tests/test_delegacao.py::test_should_delegate_programa - ImportError: cannot import name 'should_delegate'
```

- [ ] **Step 3: Write minimal implementation**

`backend/delegacao.py`:
```python
"""delegacao.py — política de delegação automática Claude → Codex.

Detecta tarefas de execução pura (programar, refatorar, rodar) e as roteia pro
Codex sem classificação LLM (economia). Tarefas ambíguas caem numa rota leve no
orchestrator. Sempre injeta preâmbulo de guarda: sem git commit/push.
"""
import re
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]

# Lista de verbos inequívocos de execução (conservadora, pra minimizar falso-positivo)
EXEC_VERBS = [
    "programa", "programar", "implementa", "implementar",
    "refatora", "refatorar",
    "roda", "rodar", "executa", "executar",
    "cria", "criar", "gera", "gerar",
    "corrige", "corrigir", "fix", "fixa", "fixar",
    "testa", "testar",
    "debug", "debugar",
]

# Regex: verbo no início ou após alguns caracteres, case-insensitive
_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(v) for v in EXEC_VERBS) + r')\b',
    re.IGNORECASE
)


def enabled() -> bool:
    """Retorna True se JAVIS_AUTO_CODEX está ligado (default False)."""
    import os
    return os.environ.get("JAVIS_AUTO_CODEX", "").lower() in ("1", "true", "yes", "on")


def should_delegate(texto: str) -> bool:
    """Detecta se a tarefa é execução pura (verbo inequívoco) → delega pro Codex."""
    texto = (texto or "").strip()
    if not texto:
        return False
    return bool(_PATTERN.search(texto))


def montar_brief(texto: str, plano: str = "") -> str:
    """Monta o objetivo + preâmbulo de guarda pro Codex.
    
    Preâmbulo: "não faça git commit nem push; deixe no working tree"
    (honra o CLAUDE.md: commit/push continuam manuais).
    """
    brief_parts = [
        "⚠️ GUARDRAILS:",
        "- Não faça `git commit` nem `git push` — deixe as mudanças no working tree para revisão.",
        "- Trabalhe na pasta do projeto (raiz: " + str(JAVIS_ROOT) + ").",
        "",
        "TAREFA:",
        texto,
    ]
    if plano:
        brief_parts.insert(5, "")
        brief_parts.insert(6, "CONTEXTO (do planejamento):")
        brief_parts.insert(7, plano)
    return "\n".join(brief_parts)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd C:\Users\noteacer\Desktop\javis\_apps\javis-local-interface
python -m pytest tests/test_delegacao.py -v
```

Expected output:
```
PASSED tests/test_delegacao.py::test_should_delegate_programa
PASSED tests/test_delegacao.py::test_should_delegate_implementa
PASSED tests/test_delegacao.py::test_should_delegate_refatora
PASSED tests/test_delegacao.py::test_should_delegate_roda
PASSED tests/test_delegacao.py::test_should_delegate_cria_arquivo
PASSED tests/test_delegacao.py::test_should_delegate_corrige_bug
PASSED tests/test_delegacao.py::test_should_delegate_normal_pergunta
PASSED tests/test_delegacao.py::test_should_delegate_raciocinio
PASSED tests/test_delegacao.py::test_should_delegate_planning
```

- [ ] **Step 5: Test montar_brief()**

Add to `tests/test_delegacao.py`:
```python
from backend.delegacao import montar_brief

def test_montar_brief_sem_plano():
    """montar_brief inclui preâmbulo de guarda."""
    result = montar_brief("programa uma função")
    assert "GUARDRAILS" in result
    assert "git commit" in result
    assert "git push" in result
    assert "programa uma função" in result

def test_montar_brief_com_plano():
    """montar_brief com plano inclui contexto."""
    result = montar_brief("programa X", plano="Use o algoritmo Y")
    assert "GUARDRAILS" in result
    assert "CONTEXTO" in result
    assert "algoritmo Y" in result
```

```bash
python -m pytest tests/test_delegacao.py::test_montar_brief_sem_plano tests/test_delegacao.py::test_montar_brief_com_plano -v
```

Expected: PASSED

- [ ] **Step 6: Test enabled() com env var**

Add to `tests/test_delegacao.py`:
```python
import os
from backend.delegacao import enabled

def test_enabled_default_false():
    """JAVIS_AUTO_CODEX default False."""
    os.environ.pop("JAVIS_AUTO_CODEX", None)
    assert enabled() is False

def test_enabled_true():
    """JAVIS_AUTO_CODEX=1 returns True."""
    os.environ["JAVIS_AUTO_CODEX"] = "1"
    assert enabled() is True
    os.environ.pop("JAVIS_AUTO_CODEX")

def test_enabled_case_insensitive():
    """JAVIS_AUTO_CODEX=true (case-insensitive)."""
    os.environ["JAVIS_AUTO_CODEX"] = "TRUE"
    assert enabled() is True
    os.environ.pop("JAVIS_AUTO_CODEX")
```

```bash
python -m pytest tests/test_delegacao.py::test_enabled_default_false tests/test_delegacao.py::test_enabled_true tests/test_delegacao.py::test_enabled_case_insensitive -v
```

Expected: PASSED

- [ ] **Step 7: Commit**

```bash
git add backend/delegacao.py tests/test_delegacao.py
git commit -m "feat: delegacao.py — política de detecção de execução e brief

- should_delegate() detecta verbos inequívocos (programa, refatora, roda, etc)
- montar_brief() monta objetivo + preâmbulo de guarda (sem git commit/push)
- enabled() respeita JAVIS_AUTO_CODEX flag (default False)
- testes offline, nenhuma chamada real

Reusa code_agent, brain_switch existentes. Próximo: rota exec no orchestrator."
```

---

## Task 2: `brain_switch.py` — override engine parameter

**Files:**
- Modify: `backend/brain_switch.py:53-76` (função dispatch)

- [ ] **Step 1: Review current dispatch signature**

Read `backend/brain_switch.py` lines 53-76 to understand current signature:

```python
def dispatch(task: str, pasta: str | None = None):
    """Despacha a tarefa de programação pro motor ativo (com fallback pro outro)."""
    import claude_exec
    import code_agent

    engine = get_active()
    # ...
```

- [ ] **Step 2: Edit dispatch to accept optional engine parameter**

`backend/brain_switch.py`, replace the dispatch function (lines 53-76):

```python
def dispatch(task: str, pasta: str | None = None, engine: str | None = None):
    """Despacha a tarefa de programação pro motor ativo (com fallback pro outro).
    
    Args:
        task: descrição da tarefa
        pasta: pasta de trabalho (opcional)
        engine: força um motor específico ("claude" ou "codex"); se None, usa get_active()
    """
    import claude_exec
    import code_agent

    if engine and engine not in ("claude", "codex"):
        raise ValueError(f"engine deve ser 'claude' ou 'codex', recebido: {engine!r}")
    
    engine = engine or get_active()
    primary, fallback = (claude_exec, code_agent) if engine == "claude" else (code_agent, claude_exec)

    kwargs = {"pasta": pasta} if pasta else {}
    if primary.available():
        try:
            result = primary.dispatch(task, **kwargs)
        except TypeError:
            result = primary.dispatch(task)
        # Se Codex executou, agenda vistoria do Claude Code
        if engine == "codex" and claude_exec.available():
            threading.Thread(target=_audit_after_codex, args=(pasta,), daemon=True).start()
        return result
    if fallback.available():
        try:
            return fallback.dispatch(task, **kwargs)
        except TypeError:
            return fallback.dispatch(task)
    return "Nem Claude Code nem Codex estão disponíveis agora, senhor."
```

- [ ] **Step 3: Write test para engine override**

`tests/test_brain_switch.py` (new file):

```python
import pytest
from unittest.mock import patch, MagicMock
from backend import brain_switch

def test_dispatch_engine_override_codex():
    """engine='codex' força Codex mesmo que get_active() retorne claude."""
    with patch("backend.brain_switch.get_active", return_value="claude"):
        with patch("backend.code_agent.available", return_value=True):
            with patch("backend.code_agent.dispatch", return_value="Codex roou") as mock_codex:
                result = brain_switch.dispatch("programa X", engine="codex")
                assert mock_codex.called
                assert result == "Codex roou"

def test_dispatch_engine_none_uses_active():
    """engine=None usa get_active() normal."""
    with patch("backend.brain_switch.get_active", return_value="claude"):
        with patch("backend.claude_exec.available", return_value=True):
            with patch("backend.claude_exec.dispatch", return_value="Claude rodou") as mock_claude:
                result = brain_switch.dispatch("programa X", engine=None)
                assert mock_claude.called
                assert result == "Claude rodou"

def test_dispatch_engine_invalid():
    """engine inválida lança ValueError."""
    with pytest.raises(ValueError, match="engine deve ser"):
        brain_switch.dispatch("X", engine="invalid")
```

```bash
python -m pytest tests/test_brain_switch.py -v
```

Expected: PASSED

- [ ] **Step 4: Commit**

```bash
git add backend/brain_switch.py tests/test_brain_switch.py
git commit -m "feat: brain_switch.dispatch — engine parameter pra forçar motor

- Novo parâmetro engine (opcional): força 'claude' ou 'codex'
- Se None, usa get_active() (comportamento atual)
- Validação: ValueError se engine inválido
- Auditoria _audit_after_codex mantida
- testes com mocks, zero chamadas reais"
```

---

## Task 3: `orchestrator.py` — adicionar rota `exec`

**Files:**
- Modify: `backend/orchestrator.py:20-54, 87-132`

- [ ] **Step 1: Update SYSTEM_ORCHESTRATOR para incluir 'exec' como brain válido**

`backend/orchestrator.py`, edit SYSTEM_ORCHESTRATOR (line 20-54):

Replace:
```python
{
  "intent": "<o que o usuário quer em 2-4 palavras>",
  "complexity": "simple|medium|complex",
  "brain": "main|conclave|squad|memory",
```

With:
```python
{
  "intent": "<o que o usuário quer em 2-4 palavras>",
  "complexity": "simple|medium|complex",
  "brain": "main|conclave|squad|memory|exec",
```

And add to the rules section (after line 46):
```
- exec:      tarefa de execução pura (programar, rodar, refatorar) → delega pro Codex
```

- [ ] **Step 2: Update OrchestrationResult dataclass para incluir `exec_running`**

`backend/orchestrator.py`, edit OrchestrationResult (lines 70-85):

Add after line 84:
```python
    exec_running: bool = False  # True se Codex foi despachado
```

- [ ] **Step 3: Add _run_exec method ao Orchestrator class**

`backend/orchestrator.py`, add after `_memory_brain` method (after line 175):

```python
    def _run_exec(self, text: str, plano: str = "") -> tuple[str, bool]:
        """Roteia pra Codex via brain_switch com guardrails."""
        from delegacao import montar_brief
        import brain_switch
        
        brief = montar_brief(text, plano)
        response = brain_switch.dispatch(brief, engine="codex")
        # Retorna resposta + flag de que Codex foi despachado
        return response, True
```

- [ ] **Step 4: Update process() method para chamar _run_exec**

`backend/orchestrator.py`, edit process() (lines 91-132):

After line 108 (no final do bloco que lê o `plan`), add:

```python
        # Atalho determinístico: se should_delegate, roteia pro Codex sem classificar
        if result.requires_action is False and result.action_intent is None:
            from delegacao import enabled, should_delegate
            if enabled() and should_delegate(user_input):
                response, _ = self._run_exec(user_input, "")
                result.response = response
                result.brain = "exec"
                result.exec_running = True
                return result
```

Then edit the brain routing (lines 114-126):

Replace:
```python
        brain = result.brain

        if brain == "memory":
            result.response = self._memory_brain(user_input, result)

        elif brain == "squad" or (brain == "main" and len(result.agents_used) >= 2):
            result.response, result.squad_result = self._run_squad(user_input, result)

        elif brain == "conclave" or result.complexity == "complex":
            result.response, result.conclave_result = self._run_conclave(user_input, result)

        else:
            result.response = self._main_brain(user_input, history or [])
```

With:
```python
        brain = result.brain

        if brain == "exec":
            result.response, result.exec_running = self._run_exec(user_input, result.plan)

        elif brain == "memory":
            result.response = self._memory_brain(user_input, result)

        elif brain == "squad" or (brain == "main" and len(result.agents_used) >= 2):
            result.response, result.squad_result = self._run_squad(user_input, result)

        elif brain == "conclave" or result.complexity == "complex":
            result.response, result.conclave_result = self._run_conclave(user_input, result)

        else:
            result.response = self._main_brain(user_input, history or [])
```

- [ ] **Step 5: Write test para rota exec com atalho**

`tests/test_orchestrator_exec.py` (new file):

```python
import pytest
from unittest.mock import patch, MagicMock
from backend.orchestrator import Orchestrator

def test_orchestrator_atalho_should_delegate():
    """Atalho: should_delegate=True → _run_exec direto, sem _classify."""
    orch = Orchestrator()
    
    with patch("backend.delegacao.enabled", return_value=True):
        with patch("backend.delegacao.should_delegate", return_value=True):
            with patch.object(orch, "_run_exec", return_value=("Codex rodou", True)) as mock_exec:
                with patch.object(orch, "_classify") as mock_classify:
                    result = orch.process("programa uma função")
                    
                    # Prova: _run_exec foi chamado, _classify NÃO
                    assert mock_exec.called
                    assert not mock_classify.called
                    assert result.brain == "exec"
                    assert result.exec_running is True

def test_orchestrator_brain_exec_from_classify():
    """Classificador marca brain='exec' → _run_exec chamado."""
    orch = Orchestrator()
    
    with patch("backend.delegacao.enabled", return_value=True):
        with patch("backend.delegacao.should_delegate", return_value=False):  # Atalho não bate
            with patch.object(orch, "_classify", return_value={
                "intent": "código",
                "complexity": "simple",
                "brain": "exec",
                "plan": "refatora X"
            }):
                with patch.object(orch, "_run_exec", return_value=("Codex rodou", True)) as mock_exec:
                    result = orch.process("refatora o código")
                    
                    # Classificador foi chamado, depois _run_exec
                    assert mock_exec.called
                    assert result.brain == "exec"

def test_orchestrator_delegacao_disabled():
    """Com JAVIS_AUTO_CODEX=0, nada muda — comportamento atual."""
    orch = Orchestrator()
    
    with patch("backend.delegacao.enabled", return_value=False):
        with patch.object(orch, "_classify", return_value={
            "intent": "conversa",
            "complexity": "simple",
            "brain": "main"
        }):
            with patch.object(orch, "_main_brain", return_value="Resposta") as mock_main:
                result = orch.process("olá")
                
                # Comportamento intacto
                assert mock_main.called
                assert result.brain == "main"
```

```bash
python -m pytest tests/test_orchestrator_exec.py -v
```

Expected: PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/orchestrator.py tests/test_orchestrator_exec.py
git commit -m "feat: orchestrator — rota exec pro Codex via delegacao

- SYSTEM_ORCHESTRATOR inclui 'exec' como brain
- _run_exec(text, plano) roteia pro Codex com guardrails (brief + no git)
- Atalho: delegacao.should_delegate() evita _classify pra verbos óbvios (economia)
- Fallback: resposta_type=='code' também roteia pro exec (classificador leve)
- JAVIS_AUTO_CODEX=0 → comportamento intacto
- testes com mocks, zero LLM"
```

---

## Task 4: `_skills/delegar-execucao.md` — documentação da política

**Files:**
- Create: `_skills/delegar-execucao.md`

- [ ] **Step 1: Write the skill documentation**

`_skills/delegar-execucao.md`:

```markdown
# Skill: Delegar Execução pro Codex

## O quê
Detecta automaticamente tarefas de execução (programação, testes, refatoração) e as
delega pro Codex (seu "segundo programador") em vez de o Claude fazer tudo.
**O Claude é o cérebro (arquitetura/raciocínio); o Codex são as mãos (execução).**

## Por quê
Economia de cota do Claude. Você paga pelo Claude (assinatura); Codex é outra
assinatura que já tem. Deixa o raciocínio caro no Claude, execução no Codex.
O Claude audita o resultado do Codex depois (via `_audit_after_codex`).

## Como ativa
```bash
# No seu shell, antes de rodar o Javis:
set JAVIS_AUTO_CODEX=1

# Ou via Claude Code:
set JAVIS_AUTO_CODEX=true
```

**Default:** desligado (`JAVIS_AUTO_CODEX=0` ou não definida).

## O que dispara delegação

### Atalho (zero LLM, rápido) — tarefas óbvias
Verbo inequívoco no começo/meio da tarefa:
- "**programa** uma função que..." ✓ delegado
- "**implementa** o algoritmo de..." ✓ delegado
- "**refatora** o arquivo X" ✓ delegado
- "**roda** os testes do projeto" ✓ delegado
- "**cria** o arquivo main.py" ✓ delegado
- "**corrige** o bug na linha 42" ✓ delegado
- "**testa** a integração" ✓ delegado

### Via classificador (LLM leve) — tarefas ambíguas
Se a tarefa não bate no atalho, o Claude classifica leve:
- Input: "Analisando o projeto, você vê que o módulo X precisa refatoração. Faça."
- Classificador marca `response_type: "code"` ou `brain: "exec"`
- Resultado: roteia pro Codex

### NÃO delega (Claude mantém) — raciocínio
- "qual é a melhor arquitetura para..." ✗ Claude fica
- "explica como este código funciona" ✗ Claude fica
- "monta um plano pra..." ✗ Claude fica
- "analisa este log e diz o que significa" ✗ Claude fica

## Guardrails (automáticos)

Toda tarefa delegada chega ao Codex com este preâmbulo:
```
⚠️ GUARDRAILS:
- Não faça `git commit` nem `git push` — deixe as mudanças no working tree para revisão.
- Trabalhe na pasta do projeto...
```

**Por quê:** seu `CLAUDE.md` é rígido em segurança. Codex mexe nos arquivos, mas
commit/push continuam manuais. O Claude audita tudo depois.

## Fluxo completo

```
Você fala: "programa uma função que..."
         ↓
should_delegate() vê "programa" ✓
         ↓
delegacao.montar_brief() monta: objetivo + guardrails
         ↓
brain_switch.dispatch(brief, engine="codex")
         ↓
code_agent roda: codex exec <brief> (working tree, streaming)
         ↓
_audit_after_codex (Claude audita resultado e te notifica)
```

## Customizar (editar esta skill)

Para mudar quais verbos disparam delegação, edite a lista `EXEC_VERBS` em
`backend/delegacao.py` — depois rode os testes:

```bash
pytest tests/test_delegacao.py -v
```

Se adicionar um verbo, a skill não precisa atualizar (o código é a fonte-da-verdade).

## Debugging

**Ver se está ativo:**
```bash
python -c "import os; print(os.environ.get('JAVIS_AUTO_CODEX', 'não definida'))"
```

**Forçar Claude mesmo com tarefa de execução:**
```bash
set JAVIS_AUTO_CODEX=0
# rodar Javis normalmente
```

**Ver o brief que vai pro Codex:**
Rode os testes em `tests/test_delegacao.py::test_montar_brief_*` — eles mostram
exatamente o que o Codex recebe.
```

- [ ] **Step 2: Verify the skill is readable**

```bash
cat _skills/delegar-execucao.md | wc -l
# Expected: ~120 linhas (documento compacto mas completo)
```

- [ ] **Step 3: Commit**

```bash
git add _skills/delegar-execucao.md
git commit -m "docs: skill delegar-execucao.md — política de delegação

Documentação em linguagem humana (Murillo edita aqui):
- O quê, por quê, como ativa
- Verbos que disparam atalho (sem LLM)
- Guardrails automáticos (sem git commit/push)
- Fluxo completo
- Como customizar e debugar"
```

---

## Task 5: Testes de integração (delegacao + orchestrator)

**Files:**
- Modify: `tests/test_orchestrator_exec.py` (add mais testes)

- [ ] **Step 1: Write test do fluxo completo (com mocks)**

Add to `tests/test_orchestrator_exec.py`:

```python
def test_full_flow_atalho_to_codex():
    """Fluxo completo: input → should_delegate → _run_exec → Codex."""
    orch = Orchestrator()
    
    with patch("backend.delegacao.enabled", return_value=True):
        with patch("backend.delegacao.should_delegate", return_value=True):
            with patch("backend.brain_switch.dispatch") as mock_dispatch:
                mock_dispatch.return_value = "✓ Função criada e testada."
                
                result = orch.process("programa uma função que faz sort")
                
                # Verifica chamada ao dispatch com engine="codex"
                assert mock_dispatch.called
                call_args = mock_dispatch.call_args
                assert call_args.kwargs.get("engine") == "codex"
                assert "GUARDRAILS" in call_args.args[0]  # brief tem guardrails
                assert "sem git commit" in call_args.args[0].lower()

def test_disabled_ignores_should_delegate():
    """Com JAVIS_AUTO_CODEX=0, should_delegate é ignorado."""
    orch = Orchestrator()
    
    with patch("backend.delegacao.enabled", return_value=False):
        with patch("backend.delegacao.should_delegate", return_value=True):  # Mesmo que bata
            with patch.object(orch, "_classify", return_value={
                "intent": "conversa",
                "complexity": "simple",
                "brain": "main"
            }):
                with patch.object(orch, "_main_brain", return_value="Claude responde"):
                    result = orch.process("programa X")
                    
                    # _main_brain foi chamado, não Codex
                    assert result.brain == "main"
```

```bash
python -m pytest tests/test_orchestrator_exec.py::test_full_flow_atalho_to_codex tests/test_orchestrator_exec.py::test_disabled_ignores_should_delegate -v
```

Expected: PASSED

- [ ] **Step 2: Commit**

```bash
git add tests/test_orchestrator_exec.py
git commit -m "test: testes de integração delegacao + orchestrator

- Atalho → dispatch com engine='codex' e guardrails no brief
- Flag disabled → comportamento intacto
- Todos com mocks, zero LLM real"
```

---

## Task 6: Verificação end-to-end (manual, com flag ligado)

**Files:**
- None (verificação manual)

- [ ] **Step 1: Set flag e rodar o Javis**

```bash
set JAVIS_AUTO_CODEX=1
cd C:\Users\noteacer\Desktop\javis\_apps\javis-local-interface
python backend/server.py
```

Expected: Servidor sobe e responde em `http://localhost:8000/status`.

- [ ] **Step 2: Teste no navegador ou via curl**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"input":"programa uma função que retorna fibonacci", "history":[]}'
```

Expected response: algo como `"brain": "exec", "response": "Codex rodando..."`

Verificar também:
- Logs do servidor (na janela onde o Python está rodando) mostram `_run_exec` sendo chamado
- Aba Execução no Javis exibe o streaming do Codex ao vivo

- [ ] **Step 3: Teste com flag desligado**

```bash
set JAVIS_AUTO_CODEX=0
# rodar o servidor novamente
```

Expected: mesma pergunta agora roteia pro `main` (Claude), não pro Codex.

- [ ] **Step 4: Teste classificador (tarefas ambíguas)**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"input":"Analisando o projeto, o módulo X precisa refatoração. Execute.", "history":[]}'
```

Expected: classificador emite `response_type: "code"` → roteia pro Codex mesmo sem atalho.

- [ ] **Step 5: Verificar auditoria (voz do Claude depois)**

Após Codex rodar e terminar, verificar que:
- `_audit_after_codex` é disparado em background
- Claude audita o resultado em ~5-10s (notificação via Telegram/reminder)
- Mensagem de auditoria aparece no Javis

---

## Self-Review

**Spec coverage:**
- ✓ Gatilho (Claude decide sozinho) → implementado via should_delegate + orchestrator
- ✓ Divisão (objetivo → Codex faz tudo → Claude audita) → delegacao.montar_brief + reuso _audit_after_codex
- ✓ Autonomia (Codex mexe livre, Claude audita depois) → guardrails no brief (sem commit/push)
- ✓ Abordagem híbrida (C: atalho + A: classificador + B: skill) → delegacao.py + orchestrator.py + _skills/delegar-execucao.md
- ✓ Flag JAVIS_AUTO_CODEX (default desligado) → enabled() em delegacao.py
- ✓ Reusar (code_agent, brain_switch, _audit_after_codex) → nenhuma duplicação
- ✓ Testes offline com mock → todos em test_delegacao.py, test_brain_switch.py, test_orchestrator_exec.py

**Placeholder scan:**
- Nenhum "TBD", "TODO", "fill in", "add error handling"
- Todo passo tem código real, comando exato, expected output
- Tipos são consistentes em todas as tasks (engine: "claude" | "codex", etc.)

**Type consistency:**
- `should_delegate() → bool` (Task 1, usado em Task 3)
- `montar_brief(texto, plano="") → str` (Task 1, usado em Task 3)
- `enabled() → bool` (Task 1, usado em Task 3)
- `dispatch(..., engine=None)` (Task 2, chamado em Task 3)
- `_run_exec(text, plano="") → tuple[str, bool]` (Task 3, consistente)

All files match spec: delegacao.py ✓, orchestrator.py ✓, brain_switch.py ✓, skill ✓.

---

## Plan Complete

Plan saved to `_docs/JAVIS-DELEGACAO-CODEX-PLAN.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** — I spawn a fresh subagent per task, review between tasks, fast iteration and parallel work.

**2. Inline Execution** — Execute tasks in this session sequentially with checkpoints for you to review after each task batch.

Which approach would you prefer?
