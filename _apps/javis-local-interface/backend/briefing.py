"""briefing.py — ponte de ESTADO do projeto para o cérebro do Javis.

Resolve a lacuna em que o Javis não sabia "o que a gente fez": lê as fontes
de verdade do projeto (estado atual, último log, decisões e pendências) e
monta um resumo conciso e factual. Esse resumo é:

  1. injetado no system prompt do agente (`agent._system`) → todo cérebro
     (voz e chat) passa a conhecer o estado sem precisar acionar ferramenta;
  2. servido em /briefing para a interface dar a saudação proativa ao abrir.

Tudo degrada com elegância: se um arquivo não existir, simplesmente não entra.
Cacheado por alguns segundos para não reler o disco a cada token.
"""
from __future__ import annotations
import re
import time
from datetime import datetime
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]
ESTADO_DIR = JAVIS_ROOT / "_estado"
LOGS_DIR   = JAVIS_ROOT / "_logs"
MEMORIA_DIR = JAVIS_ROOT / "_memoria"

_CACHE: dict[str, object] = {"ts": 0.0, "estado": "", "saudacao": ""}
_TTL = 15  # segundos


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


# R2.2.1 — CURRENT_STATE.md é a FONTE CANÔNICA do estado. Quando existe, prevalece
# sobre os roadmaps antigos (estado-atual.md / proximos-passos.md / _logs) ao
# responder "estado atual / próximas fases / o que falta / próximo passo".
def _current_state(max_chars: int = 1100) -> str:
    """Conteúdo canônico de _estado/CURRENT_STATE.md (ou '' se não existir)."""
    txt = _read(ESTADO_DIR / "CURRENT_STATE.md").strip()
    return txt[:max_chars] if txt else ""


def _proximo_passo_oficial() -> str:
    """Extrai o 'PRÓXIMO PASSO OFICIAL' do CURRENT_STATE.md (linha em negrito
    logo após o cabeçalho). '' se o arquivo/seção não existir."""
    txt = _read(ESTADO_DIR / "CURRENT_STATE.md")
    if not txt:
        return ""
    m = re.search(r"PR(Ó|O)XIMO PASSO OFICIAL.*?\n+\s*\*\*(.+?)\*\*", txt, re.S | re.I)
    return m.group(2).strip() if m else ""


def _ultimas_sessoes(n: int = 3) -> list[str]:
    """As N linhas mais recentes da seção 'Sessões recentes' do estado-atual."""
    txt = _read(ESTADO_DIR / "estado-atual.md")
    if not txt:
        return []
    # pega o bloco a partir do cabeçalho 'Sessões recentes'
    m = re.search(r"##\s*Sess(õ|o)es recentes(.+?)(\n##\s|\Z)", txt, re.S | re.I)
    bloco = m.group(2) if m else txt
    linhas = [l.strip() for l in bloco.splitlines() if l.strip().startswith("- ")]
    # trunca cada linha para o briefing ficar conciso (não estourar o contexto)
    enxutas = []
    for l in linhas[-n:]:
        l = re.sub(r"`|\*\*", "", l)
        if len(l) > 170:
            l = l[:167].rstrip() + "…"
        enxutas.append(l)
    return enxutas


def _ultimo_log() -> tuple[str, str]:
    """Título e data do log mais recente em _logs/ (ignora token-economy)."""
    if not LOGS_DIR.is_dir():
        return "", ""
    logs = [f for f in LOGS_DIR.glob("*.md") if "token-economy" not in f.name]
    if not logs:
        return "", ""
    recente = max(logs, key=lambda f: f.stat().st_mtime)
    txt = _read(recente)
    titulo = ""
    for linha in txt.splitlines():
        if linha.startswith("# "):
            titulo = linha[2:].strip()
            break
    # remove prefixos genéricos ('Decisão:', 'Log:') para a frase fluir
    titulo = re.sub(r"^(Decis(ã|a)o|Log|Registro)\s*:\s*", "", titulo, flags=re.I)
    data = recente.name[:10]
    return titulo or recente.stem, data


def _pendencias(n: int = 4) -> list[str]:
    """Itens em aberto ('- [ ]') de proximos-passos.md."""
    txt = _read(ESTADO_DIR / "proximos-passos.md")
    if not txt:
        return []
    itens = re.findall(r"-\s*\[\s*\]\s*(.+)", txt)
    return [re.sub(r"`|\*\*", "", i).strip()[:90] for i in itens[:n]]


def _periodo() -> str:
    h = datetime.now().hour
    if h < 12:
        return "Bom dia"
    if h < 18:
        return "Boa tarde"
    return "Boa noite"


def estado_resumido(max_chars: int = 2200) -> str:
    """Resumo factual do estado do projeto para injetar no contexto do cérebro."""
    now = time.time()
    if now - float(_CACHE["ts"]) < _TTL and _CACHE["estado"]:
        return str(_CACHE["estado"])

    partes: list[str] = []

    # FONTE CANÔNICA primeiro: prevalece sobre os roadmaps antigos abaixo.
    canonico = _current_state()
    if canonico:
        partes.append(
            "ESTADO CANÔNICO (fonte de verdade — _estado/CURRENT_STATE.md; "
            "prevalece sobre roadmaps antigos ao dizer estado atual / próximas "
            "fases / o que falta / próximo passo):"
        )
        partes.append(canonico)
        partes.append("--- Contexto histórico (secundário; só se o canônico não cobrir) ---")

    titulo, data = _ultimo_log()
    if titulo:
        partes.append(f"Último registro de trabalho ({data}): {titulo}.")

    sessoes = _ultimas_sessoes(3)
    if sessoes:
        partes.append("Sessões recentes:")
        partes.extend(f"  {s}" for s in sessoes)

    pend = _pendencias(4)
    if pend:
        partes.append("Pendências em aberto: " + "; ".join(pend) + ".")

    texto = "\n".join(partes).strip()[:max_chars]
    _CACHE.update(ts=now, estado=texto)
    return texto


def saudacao_proativa() -> str:
    """Saudação curta e proativa para a interface falar/mostrar ao abrir."""
    titulo, data = _ultimo_log()
    base = f"{_periodo()}, senhor."
    if titulo:
        base += f" No nosso último trabalho ({data}), {titulo[0].lower() + titulo[1:]}."
    # Próximo passo: o canônico (CURRENT_STATE.md) prevalece sobre pendências antigas.
    passo = _proximo_passo_oficial()
    if passo:
        base += f" Próximo passo oficial: {passo}."
    else:
        pend = _pendencias(2)
        if pend:
            base += f" Em aberto: {pend[0]}."
    return base


def briefing_dict() -> dict:
    return {
        "saudacao": saudacao_proativa(),
        "estado": estado_resumido(),
        "hora": datetime.now().strftime("%H:%M"),
    }
