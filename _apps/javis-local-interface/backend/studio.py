"""studio.py — agente Estúdio em MODO SEGURO.

Produz um PACOTE TEXTUAL de criativos a partir da pauta aprovada
(`pauta-semana.md`), salva em `criativos-semana.md`, registra o Journey Log e
cria o Gate 2 pra aprovação do Murillo.

MODO SEGURO: não gera imagem, não publica, não chama integração externa. O
conteúdo é montado por TEMPLATE LOCAL lendo a pauta (sem LLM/cota) — toda peça
visual fica marcada como [CONFIRMAR COM MURILLO] / a produzir via plugin.
Idempotente: se os criativos e o Gate 2 já existem, não duplica.
"""
from __future__ import annotations
import re
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]
CJ = JAVIS_ROOT / "_projetos" / "cerebro-jampa"
PAUTA = CJ / "posts" / "pauta-semana.md"
CRIATIVOS = CJ / "posts" / "criativos-semana.md"

_DESIGN_TASK = "pipeline-marketing-vem-passear-jampa-t2"
_GATE2_SUBJECT = "Aprovar criativos da semana antes de publicar"


def is_design_task(task: dict) -> bool:
    """É a task de Design do pipeline VP?"""
    if not task:
        return False
    if task.get("ext_id") == _DESIGN_TASK:
        return True
    return (task.get("title") or "").strip().lower().startswith("[design]")


def _extrai_posts(pauta_txt: str) -> list[dict]:
    """Extrai os posts da pauta (heurística simples por '## POST')."""
    blocos = re.split(r"\n##\s+POST", pauta_txt, flags=re.IGNORECASE)
    posts = []
    for b in blocos[1:]:  # [0] é o cabeçalho antes do 1º POST
        head = b.splitlines()[0].strip(" —-") if b.strip() else ""

        def _pega(rotulo):
            m = re.search(rf"{rotulo}[^\n:]*:\*?\*?\s*(.+)", b, flags=re.IGNORECASE)
            return m.group(1).strip(" *") if m else ""

        posts.append({
            "titulo":  f"POST {head}"[:80],
            "pilar":   _pega("Pilar"),
            "formato": _pega("Formato"),
            "gancho":  _pega("Gancho"),
            "cta":     _pega("CTA"),
        })
    return posts[:3]


def _template_criativos(posts: list[dict]) -> str:
    import time
    out = [
        "# Criativos da Semana — Vem Passear Jampa",
        f"\n> Pacote textual gerado pelo Estúdio (modo seguro) via Javis, "
        f"{time.strftime('%Y-%m-%d %H:%M')}.",
        "> SEM imagem gerada, SEM publicação. Peças visuais via plugin Adobe/Canva "
        "a partir das fotos do Murillo. Próximo: Gate 2 (aprovação).\n",
    ]
    if not posts:
        out.append("> ⚠️ Não encontrei posts na pauta-semana.md — "
                   "[CONFIRMAR COM MURILLO: gerar/conferir a pauta primeiro].\n")
        posts = [{"titulo": f"POST {i}", "pilar": "", "formato": "", "gancho": "", "cta": ""}
                 for i in (1, 2, 3)]
    for i, p in enumerate(posts, 1):
        gancho = p["gancho"] or "[CONFIRMAR COM MURILLO: gancho/headline]"
        cta = p["cta"] or "[CONFIRMAR COM MURILLO: CTA]"
        formato = p["formato"] or "[CONFIRMAR COM MURILLO: formato]"
        out += [
            f"\n---\n\n## Peça {i} — {p['titulo']}",
            f"- **Ideia de post:** {p['pilar'] or '[CONFIRMAR COM MURILLO: ângulo]'} — "
            f"transformar o gancho da pauta numa peça {formato}.",
            f"- **Headline:** {gancho}",
            f"- **Legenda:** usar a legenda da pauta-semana.md (Post {i}); ajustar a "
            f"quebra de linha pra leitura no feed. [CONFIRMAR COM MURILLO: ajustes finos]",
            f"- **CTA:** {cta}",
            "- **Briefing visual:** "
            f"formato {formato}; cores/identidade da marca; arte limpa (1 ideia por "
            "peça). [CONFIRMAR COM MURILLO: quais fotos/vídeos usar de "
            "`imagens/_FOTOS-AQUI/`].",
            "- **Story/Reels:** abrir com a imagem mais forte nos 3s; sticker de "
            "enquete/pergunta; CTA pro WhatsApp no último frame.",
        ]
    out += [
        "\n---\n\n## Observações pendentes",
        "- [CONFIRMAR COM MURILLO: selecionar as fotos/vídeos reais por peça].",
        "- [CONFIRMAR COM MURILLO: validar maré/vaga/preço de qualquer peça de oferta].",
        "- [CONFIRMAR COM MURILLO: datas exatas de publicação].",
        "\n**Status: criativos propostos — aguardando aprovação do Murillo (Gate 2).**\n",
    ]
    return "\n".join(out)


def gerar_criativos_vp(task_id: str) -> str:
    """Lê a pauta e gera o pacote textual de criativos. Retorna o caminho salvo."""
    pauta_txt = PAUTA.read_text(encoding="utf-8") if PAUTA.exists() else ""
    posts = _extrai_posts(pauta_txt)
    CRIATIVOS.parent.mkdir(parents=True, exist_ok=True)
    CRIATIVOS.write_text(_template_criativos(posts), encoding="utf-8")
    return str(CRIATIVOS)


def _gate2_pendente(task_id: str):
    import repositories as repo
    for a in repo.approvals.by_task(task_id):
        if a.get("status") == "pending" and a.get("subject") == _GATE2_SUBJECT:
            return a
    return None


def run_studio(task_id: str, actor: str = "murillo") -> dict:
    """Roda o Estúdio na task de Design: gera criativos + cria Gate 2. Idempotente."""
    import repositories as repo
    task = repo.tasks.get_task(task_id)
    if not task:
        return {"ok": False, "error": f"task '{task_id}' não encontrada"}
    if not is_design_task(task):
        return {"ok": False, "error": "esta não é a task de Design do pipeline VP"}
    if task.get("status") in ("completed", "killed"):
        return {"ok": False, "error": "task de Design já encerrada"}

    # idempotência: criativos + Gate 2 já existem → não duplica
    ja_gate = _gate2_pendente(task_id)
    if ja_gate and CRIATIVOS.exists():
        return {"ok": False, "already": True, "error": "criativos e Gate 2 já existem",
                "arquivo": str(CRIATIVOS), "gate2_id": ja_gate["id"]}

    # 1) task em andamento
    repo.tasks.set_status(task_id, "in_progress")
    # 2) Estúdio acionado
    repo.task_events.add_event(task_id, "agent_called", "agent",
                               "Estúdio acionado para produzir os criativos", agent_id="estudio")
    # 3) gera + salva o arquivo
    arquivo = gerar_criativos_vp(task_id)
    repo.task_events.add_event(task_id, "file_generated", "agent",
                               "criativos-semana.md gerado (pacote textual)", agent_id="estudio",
                               metadata={"arquivo": "_projetos/cerebro-jampa/posts/criativos-semana.md"})
    # 4) Gate 2 (se ainda não houver pendente)
    gate2_id = ja_gate["id"] if ja_gate else repo.approvals.add(
        subject=_GATE2_SUBJECT, kind="gate", agent="estudio",
        detail="_projetos/cerebro-jampa/posts/criativos-semana.md", task_id=task_id)
    repo.task_events.add_event(task_id, "approval_requested", "system",
                               "Gate 2 solicitada — aguardando aprovação do Murillo", agent_id="estudio")
    # 5) action_log
    try:
        repo.logs.add(source="frontend", intent="gerar_criativos_vp", agent="estudio",
                      message=f"Estúdio gerou criativos da semana; Gate 2 pendente (task {task_id})",
                      status="ok", approved=None)
    except Exception:
        pass

    return {"ok": True, "arquivo": arquivo, "gate2_id": gate2_id,
            "message": "Criativos gerados. Gate 2 aguardando aprovação."}
