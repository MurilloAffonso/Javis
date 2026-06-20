"""distribution.py — preparação de Distribuição em MODO SEGURO.

Quando a task de Distribuição está liberada (após Gate 2), prepara um PACOTE
TEXTUAL de publicação a partir da pauta + criativos, salva em
`distribuicao-semana.md`, registra o Journey Log e cria o Gate 3 antes de QUALQUER
publicação.

MODO SEGURO: NÃO publica, NÃO conecta WhatsApp/Instagram/GMB, NÃO chama integração
externa, NÃO gera imagem. Conteúdo por TEMPLATE LOCAL (sem LLM/cota). Idempotente.
"""
from __future__ import annotations
import re
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]
CJ = JAVIS_ROOT / "_projetos" / "cerebro-jampa"
PAUTA = CJ / "posts" / "pauta-semana.md"
CRIATIVOS = CJ / "posts" / "criativos-semana.md"
DISTRIB = CJ / "posts" / "distribuicao-semana.md"

_DIST_TASK = "vp-distribuicao-preparar"
_GATE3_SUBJECT = "Aprovar distribuição antes de publicar"


def is_distribution_task(task: dict) -> bool:
    if not task:
        return False
    if task.get("ext_id") == _DIST_TASK:
        return True
    return (task.get("title") or "").strip().lower().startswith("[distribuição] preparar")


def _posts_da_pauta(txt: str) -> list[dict]:
    blocos = re.split(r"\n##\s+POST", txt, flags=re.IGNORECASE)
    posts = []
    for b in blocos[1:]:
        head = b.splitlines()[0].strip(" —-") if b.strip() else ""

        def _pega(rotulo):
            m = re.search(rf"{rotulo}[^\n:]*:\*?\*?\s*(.+)", b, flags=re.IGNORECASE)
            return m.group(1).strip(" *") if m else ""

        posts.append({"titulo": f"POST {head}"[:80], "formato": _pega("Formato"),
                      "cta": _pega("CTA")})
    return posts[:3]


def _template_distribuicao(posts: list[dict]) -> str:
    import time
    out = [
        "# Distribuição da Semana — Vem Passear Jampa",
        f"\n> Pacote textual de distribuição gerado pelo Midas (modo seguro) via Javis, "
        f"{time.strftime('%Y-%m-%d %H:%M')}.",
        "> SEM publicação, SEM conexão com WhatsApp/Instagram/GMB. Apenas o plano. "
        "Próximo: Gate 3 (aprovação antes de publicar).\n",
        "## Calendário sugerido de publicação",
        "| Dia | Peça | Canais | Melhor horário (sugerido) |",
        "|---|---|---|---|",
    ]
    dias = ["Segunda", "Quarta", "Sexta"]
    for i, p in enumerate(posts or [{}, {}, {}], 1):
        dia = dias[i - 1] if i <= len(dias) else f"Dia {i}"
        fmt = (p.get("formato") if p else "") or "[CONFIRMAR COM MURILLO]"
        out.append(f"| {dia} | Peça {i} ({fmt}) | Feed + Stories + WhatsApp Status | "
                   f"[CONFIRMAR COM MURILLO: 11h ou 18h?] |")
    out += [
        "\n## Canais sugeridos",
        "- **Instagram Feed** — peça principal de cada dia.",
        "- **Instagram Stories** — bastidor + enquete + CTA pro WhatsApp.",
        "- **WhatsApp Status** — reforço da peça do dia pros contatos.",
        "- **Google Meu Negócio** — post da oferta/novidade (alcance local).",
        "\n## Por peça",
    ]
    for i, p in enumerate(posts or [{}, {}, {}], 1):
        cta = (p.get("cta") if p else "") or "[CONFIRMAR COM MURILLO: CTA]"
        out += [
            f"\n### Peça {i} — {(p.get('titulo') if p else '') or 'POST'}",
            "- **Legenda final sugerida:** usar a legenda de `criativos-semana.md` "
            "(Peça {0}); revisar quebras de linha. [CONFIRMAR COM MURILLO: ajuste fino]".format(i),
            f"- **CTA:** {cta}",
            "- **Melhor horário:** [CONFIRMAR COM MURILLO: confirmar janela de maior alcance].",
        ]
    out += [
        "\n## Checklist antes de publicar",
        "- [ ] Peças visuais prontas e conferidas (marca/cores).",
        "- [ ] [CONFIRMAR COM MURILLO: maré/vaga/preço de qualquer peça de oferta].",
        "- [ ] Legendas revisadas, sem promessa que dependa do clima.",
        "- [ ] CTA aponta pro WhatsApp certo.",
        "- [ ] Datas/horários confirmados.",
        "- [ ] Autorização de imagem de cliente, se houver.",
        "\n**Status: distribuição proposta — aguardando aprovação do Murillo (Gate 3).**\n",
    ]
    return "\n".join(out)


def preparar_distribuicao_vp(task_id: str) -> str:
    """Lê pauta + criativos e gera o pacote textual de distribuição."""
    pauta_txt = PAUTA.read_text(encoding="utf-8") if PAUTA.exists() else ""
    posts = _posts_da_pauta(pauta_txt)
    DISTRIB.parent.mkdir(parents=True, exist_ok=True)
    DISTRIB.write_text(_template_distribuicao(posts), encoding="utf-8")
    return str(DISTRIB)


def _gate3_pendente(task_id: str):
    import repositories as repo
    for a in repo.approvals.by_task(task_id):
        if a.get("status") == "pending" and a.get("subject") == _GATE3_SUBJECT:
            return a
    return None


def run_distribution(task_id: str, actor: str = "murillo") -> dict:
    """Prepara a Distribuição na task liberada: gera arquivo + cria Gate 3. Idempotente."""
    import repositories as repo
    task = repo.tasks.get_task(task_id)
    if not task:
        return {"ok": False, "error": f"task '{task_id}' não encontrada"}
    if not is_distribution_task(task):
        return {"ok": False, "error": "esta não é a task de Distribuição do pipeline VP"}
    if task.get("status") in ("completed", "killed"):
        return {"ok": False, "error": "task de Distribuição já encerrada"}

    ja_gate = _gate3_pendente(task_id)
    if ja_gate and DISTRIB.exists():
        return {"ok": False, "already": True, "error": "distribuição e Gate 3 já existem",
                "arquivo": str(DISTRIB), "gate3_id": ja_gate["id"]}

    repo.tasks.set_status(task_id, "in_progress")
    repo.task_events.add_event(task_id, "agent_called", "agent",
                               "Midas acionado para preparar a distribuição", agent_id="midas")
    arquivo = preparar_distribuicao_vp(task_id)
    repo.task_events.add_event(task_id, "file_generated", "agent",
                               "distribuicao-semana.md gerado (pacote textual)", agent_id="midas",
                               metadata={"arquivo": "_projetos/cerebro-jampa/posts/distribuicao-semana.md"})
    gate3_id = ja_gate["id"] if ja_gate else repo.approvals.add(
        subject=_GATE3_SUBJECT, kind="gate", agent="midas",
        detail="_projetos/cerebro-jampa/posts/distribuicao-semana.md", task_id=task_id)
    repo.task_events.add_event(task_id, "approval_requested", "system",
                               "Gate 3 solicitada — aguardando aprovação antes de publicar", agent_id="midas")
    try:
        repo.logs.add(source="frontend", intent="preparar_distribuicao_vp", agent="midas",
                      message=f"Midas preparou a distribuição; Gate 3 pendente (task {task_id})",
                      status="ok", approved=None)
    except Exception:
        pass

    return {"ok": True, "arquivo": arquivo, "gate3_id": gate3_id,
            "message": "Distribuição preparada. Gate 3 aguardando aprovação."}
