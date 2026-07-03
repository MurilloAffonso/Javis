"""wa_analyzer.py — Analisa um EXPORT de conversa do WhatsApp (arquivo .txt).

Objetivo (pedido do Murillo): entender como ele conversa/vende, achar padrões de
lead perdido e destilar uma "voz do Murillo" que vira material de treino do squad
(grounding do Nova/LNS). 100% LOCAL: roda no Claude da assinatura (claude_brain),
nada é publicado nem enviado. Contatos dos clientes ficam no texto do dono — o
resultado é análise, não vazamento.

Fluxo: parse_export → basic_stats → analyze (LLM) → opcional save_voice_doc.
"""
from __future__ import annotations
import re
from pathlib import Path
from collections import Counter
from datetime import datetime

JAVIS_ROOT = Path(__file__).resolve().parents[3]
CJ = JAVIS_ROOT / "_projetos" / "cerebro-jampa"

# Cobre Android pt-BR (`01/07/2026 14:32 - Fulano: msg`) e iOS
# (`[01/07/26, 14:32:05] Fulano: msg`). Linhas sem match = continuação da anterior.
_LINE = re.compile(
    r"^\[?(\d{1,2}/\d{1,2}/\d{2,4})[,]?\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*\]?\s*(?:-\s*)?([^:]{1,60}?):\s(.*)$"
)


def parse_export(text: str) -> list[dict]:
    """Converte o export em [{ts, sender, text}]. Junta mensagens multi-linha."""
    msgs: list[dict] = []
    for raw in (text or "").splitlines():
        m = _LINE.match(raw)
        if m:
            date, time, sender, body = m.groups()
            msgs.append({"date": date, "time": time, "sender": sender.strip(), "text": body})
        elif msgs:
            msgs[-1]["text"] += "\n" + raw
    # descarta linhas de sistema comuns do WhatsApp
    lixo = ("Mensagens e ligações são criptografadas", "as mensagens e as chamadas são",
            "criou este grupo", "mudou o assunto", "adicionou", "saiu", "<Arquivo de mídia oculto>")
    return [x for x in msgs if not any(l.lower() in x["text"].lower() for l in lixo)]


def basic_stats(msgs: list[dict], me: str = "") -> dict:
    """Estatísticas leves e determinísticas (sem LLM)."""
    if not msgs:
        return {"total": 0}
    por_pessoa = Counter(m["sender"] for m in msgs)
    quem_sou = me.strip() or (por_pessoa.most_common(1)[0][0] if por_pessoa else "")
    horas = Counter()
    for m in msgs:
        try:
            horas[int(m["time"].split(":")[0])] += 1
        except Exception:
            pass
    hora_pico = horas.most_common(1)[0][0] if horas else None
    return {
        "total": len(msgs),
        "pessoas": por_pessoa.most_common(8),
        "eu": quem_sou,
        "minhas_msgs": por_pessoa.get(quem_sou, 0),
        "periodo": f'{msgs[0]["date"]} → {msgs[-1]["date"]}',
        "hora_pico": hora_pico,
    }


def _sample(msgs: list[dict], cap_chars: int = 14000) -> str:
    """Amostra representativa (mais recente = estilo atual), limitada em chars."""
    linhas = [f'{m["sender"]}: {m["text"]}' for m in msgs]
    blob = "\n".join(linhas)
    if len(blob) <= cap_chars:
        return blob
    # pega o final (conversas recentes) — é onde está o estilo atual
    return "…(início cortado)…\n" + blob[-cap_chars:]


_SYSTEM = (
    "Você é analista sênior da Vem Passear Jampa (agência de turismo em João Pessoa/PB: "
    "piscinas naturais, catamarã, pôr do sol). Recebe um EXPORT de conversas de WhatsApp "
    "do Murillo (dono) com leads/clientes. Sua análise é INTERNA (não vai pro cliente). "
    "Responda em português do Brasil, específico e com EXEMPLOS reais citados do texto."
)


def analyze(text: str, me: str = "") -> dict:
    """Roda a análise no Claude da assinatura. Retorna {stats, analysis} ou {error}."""
    msgs = parse_export(text)
    if not msgs:
        return {"error": "Não reconheci o formato do export. Exporte a conversa pelo WhatsApp (⋮ → Mais → Exportar conversa → Sem mídia) e cole o .txt."}
    stats = basic_stats(msgs, me)
    import claude_brain
    if not claude_brain.available():
        return {"stats": stats, "error": "Claude (assinatura) indisponível agora, senhor."}
    tarefa = (
        "Analise o export de WhatsApp abaixo e produza, com títulos:\n\n"
        "## 1. Perfil de estilo do Murillo\n"
        "Tom, saudações típicas, gírias/expressões, uso de emoji, como ele dá preço, "
        "como cria urgência, como fecha. Cite 3-5 frases reais dele.\n\n"
        "## 2. O que funciona nas vendas\n"
        "Padrões que costumam levar o lead a avançar (marcar/pagar).\n\n"
        "## 3. Onde os leads travam ou somem\n"
        "Momentos em que a conversa esfria; objeções recorrentes (preço, data, indecisão) "
        "e como (ou se) ele contorna.\n\n"
        "## 4. Clientes/leads perdidos\n"
        "Casos que não fecharam e o motivo aparente.\n\n"
        "## 5. voz-murillo.md (rascunho de treino)\n"
        "Regras de tom + 5 frases-modelo + lista 'faça/não faça' para um agente escrever "
        "IGUAL ao Murillo. Este bloco vira grounding do squad.\n\n"
        f"Quem é o Murillo no export: '{stats.get('eu','')}'.\n\n"
        "=== EXPORT ===\n" + _sample(msgs)
    )
    out = claude_brain.answer(tarefa, system=_SYSTEM, timeout=240)
    if not (out or "").strip():
        return {"stats": stats, "error": "Não consegui gerar a análise agora (cota/assinatura)."}
    return {"stats": stats, "analysis": out.strip()}


def save_voice_doc(content: str) -> str:
    """Salva o material de treino como grounding do squad. Retorna o caminho relativo."""
    CJ.mkdir(parents=True, exist_ok=True)
    dest = CJ / "voz-murillo.md"
    header = (
        "# Voz do Murillo — destilada de conversas reais de WhatsApp\n"
        f"> Gerado por wa_analyzer em {datetime.now():%Y-%m-%d %H:%M}. Material de treino "
        "do squad (grounding do Nova/LNS). Revisar antes de confiar 100%.\n\n"
    )
    dest.write_text(header + (content or ""), encoding="utf-8")
    return str(dest.relative_to(JAVIS_ROOT))
