"""Test: portão de 25s da voz (janela de conversa do /v1/chat/completions).

Valida a máquina de estado do portão: responde se ouviu wake word OU se ainda
está dentro da janela de _WAKE_SESSION_SECONDS desde a última ativação. Usa o
has_wake_word REAL do voice_bridge; simula o relógio pra não depender de sleep.
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import voice_bridge as vb  # noqa: E402

WINDOW = 25.0  # espelha server._WAKE_SESSION_SECONDS

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def check(desc: str, cond: bool) -> int:
    print(f"  [{PASS if cond else FAIL}] {desc}")
    return 0 if cond else 1


def gate(user_text: str, now: float, last_wake_ts: float) -> tuple[bool, float]:
    """Réplica exata do portão (server.openai_compat). Retorna (responde?, novo_ts)."""
    woke = vb.has_wake_word(user_text)
    in_session = (now - last_wake_ts) < WINDOW
    if not (woke or in_session):
        return False, last_wake_ts
    return True, now  # ativa/renova a janela


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 55)
    print("Testes: portão de 25s da voz (janela de conversa)")
    print("=" * 55)
    fails = 0

    # Estado inicial: janela fechada (ts muito no passado)
    ts = -1000.0

    # 1) fala SEM wake word, fora da janela → silêncio
    resp, ts = gate("toca uma música aí", now=0.0, last_wake_ts=ts)
    fails += check("sem 'Javis' e fora da janela → NÃO responde", resp is False)

    # 2) fala COM wake word → responde e abre a janela
    resp, ts = gate("Javis, como tá o sistema?", now=10.0, last_wake_ts=ts)
    fails += check("'Javis' presente → responde e abre janela", resp is True and ts == 10.0)

    # 3) dentro de 25s, SEM repetir wake word → segue respondendo
    resp, ts = gate("e o backend?", now=30.0, last_wake_ts=ts)  # 20s depois
    fails += check("dentro de 25s sem repetir 'Javis' → segue respondendo", resp is True)

    # 4) conversa contínua renova a janela (novo ts a cada resposta)
    resp, ts = gate("e a voz?", now=50.0, last_wake_ts=ts)  # 20s após a anterior
    fails += check("cada frase renova a janela (papo contínuo)", resp is True and ts == 50.0)

    # 5) silêncio > 25s → janela fecha, exige 'Javis' de novo
    resp, ts = gate("qualquer fala aleatória", now=80.0, last_wake_ts=ts)  # 30s depois
    fails += check("após 25s sem 'Javis' → volta a exigir wake word (silêncio)", resp is False)

    # 6) variações reais do nome que o ASR ouve também abrem (jamba/diabes NÃO —
    # foram tirados do portão de propósito, ver voice_bridge.WAKE_WORDS)
    for w in ("Jarvis, abre o youtube", "Javes bom dia", "e aí Jávis"):
        r, _ = gate(w, now=200.0, last_wake_ts=-1000.0)
        fails += check(f"variação de wake word abre: {w!r}", r is True)
    # 'jamba' é só corte de prefixo, NÃO abre o portão sozinho
    r, _ = gate("Jamba status", now=200.0, last_wake_ts=-1000.0)
    fails += check("'Jamba' sozinho NÃO abre o portão (design)", r is False)

    print("\n" + "=" * 55)
    if fails == 0:
        print("\033[32m✅ Portão de 25s: lógica validada.\033[0m")
    else:
        print(f"\033[31m❌ {fails} caso(s) falharam.\033[0m")
    print("=" * 55)
    sys.exit(fails)


if __name__ == "__main__":
    main()
