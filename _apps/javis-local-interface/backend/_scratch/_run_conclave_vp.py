# Runner temporário — roda o Conclave sobre a estratégia da Vem Passear e salva markdown.
# Uso: python backend/_run_conclave_vp.py
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conclave

PERGUNTA = (
    "A Vem Passear Jampa é uma agência de turismo certificada (Cadastur) em João Pessoa/PB. "
    "Vende passeios de catamarã às piscinas naturais (R$60-65), Litoral Norte/Sul e combos até R$340. "
    "Vende bem PRESENCIAL, mas o digital está parado. Verba atual: só R$100. "
    "Instagram com 662 seguidores e reels de até ~2.000 views. WhatsApp Business com catálogo pronto. "
    "Murillo (dono) está sem caixa e precisa faturar rápido. "
    "Plano atual: campanha 'Maré Perfeita' (urgência REAL da maré baixa nas piscinas) com tráfego pago "
    "apontando pro WhatsApp, mais um painel 'Cérebro Vem Passear' (dentro do assistente Javis) que gera "
    "conteúdo e controla passeios e leads. "
    "PERGUNTA: qual é o caminho mais rápido e barato pra Vem Passear faturar nos próximos 30 dias, "
    "e o que o painel/Javis deve virar pra sustentar esse crescimento? "
    "Critique os riscos, ataque as suposições, e entregue um plano definitivo e priorizado."
)

PLANO_INICIAL = (
    "Gastar R$100 em ~R$20/dia por 5 dias impulsionando o reel campeão no Instagram, objetivo 'mensagens "
    "no WhatsApp', oferta isca das Piscinas R$60. Responder lead em <5min com script pronto e pedir Pix de "
    "sinal. Usar o painel Cérebro Vem Passear pra gerar conteúdo e controlar passeios/leads. Reinvestir o lucro."
)


def main():
    rounds = 2
    print(f"Rodando Conclave ({rounds} rodadas)... pode levar ~1min")
    result = conclave.Conclave().debate(PERGUNTA, PLANO_INICIAL, rounds=rounds)

    out = Path(__file__).resolve().parents[2] / "_outbox" / "2026-06-14_conclave-vem-passear.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Conclave Vem Passear — debate multi-IA")
    lines.append(f"\n*Gerado pelo Conclave do Javis ({rounds} rodadas) em "
                 f"{datetime.now().strftime('%Y-%m-%d %H:%M')} — modelo gpt-4o-mini.*\n")
    lines.append("## Pergunta\n")
    lines.append(PERGUNTA + "\n")
    lines.append("## Plano inicial avaliado\n")
    lines.append(PLANO_INICIAL + "\n")
    lines.append("---\n")
    for rd in result.get("rounds", []):
        lines.append(f"## Rodada {rd['round']}\n")
        lines.append(f"### 🔴 Crítico\n{rd['critico']}\n")
        lines.append(f"### ⚔️ Advogado\n{rd['advogado']}\n")
        lines.append(f"### ✅ Sintetizador\n{rd['synthesis']}\n")
        lines.append("---\n")
    lines.append("## 🏁 Síntese final (decisão do Conclave)\n")
    lines.append(result.get("synthesis", "(sem síntese)") + "\n")

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK -> {out}")
    print(f"Chars sintese final: {len(result.get('synthesis',''))}")


if __name__ == "__main__":
    main()
