"""Testes dos módulos novos do Jamba v2 — sem efeitos colaterais reais
(navegador, apps e arquivos são interceptados/isolados)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import command_router


# ── command_router: intents novos e prioridade ──
def test_intent_clima():
    assert command_router.route("que tempo faz hoje")["intent"] == "clima"
    assert command_router.route("vai chover?")["intent"] == "clima"

def test_musica_vence_youtube():
    # "toca musica" deve ganhar de "youtube" quando os dois aparecem
    assert command_router.route("abre o youtube e toca musica")["intent"] == "tocar_musica"

def test_youtube_puro():
    assert command_router.route("abre o youtube")["intent"] == "abrir_youtube"

def test_intent_analisar_site():
    assert command_router.route("analisa o site exemplo.com")["intent"] == "analisar_site"
    assert command_router.route("copia o site github.com")["intent"] == "analisar_site"


# ── profile (memória de personalização) ──
def test_profile_salva_lista_esquece(monkeypatch, tmp_path):
    import profile
    monkeypatch.setattr(profile, "PROFILE_FILE", tmp_path / "perfil.json")
    profile.save_fact("gosto de jazz")
    assert "gosto de jazz" in profile.list_facts()
    assert "gosto de jazz" in profile.context_block()
    # não duplica
    profile.save_fact("gosto de jazz")
    assert profile.list_facts().count("gosto de jazz") == 1
    # esquece
    profile.forget("jazz")
    assert "gosto de jazz" not in profile.list_facts()

def test_profile_vazio_sem_contexto(monkeypatch, tmp_path):
    import profile
    monkeypatch.setattr(profile, "PROFILE_FILE", tmp_path / "vazio.json")
    assert profile.context_block() == ""


# ── reminders (lembretes/timers) ──
def test_reminder_add_e_pendente(monkeypatch, tmp_path):
    import reminders
    monkeypatch.setattr(reminders, "FILE", tmp_path / "lemb.json")
    msg = reminders.add("beber agua", minutos=10)
    assert "beber agua" in msg
    pend = reminders.list_pending()
    assert any("beber agua" in p["text"] for p in pend)

def test_reminder_sem_quando(monkeypatch, tmp_path):
    import reminders
    monkeypatch.setattr(reminders, "FILE", tmp_path / "l2.json")
    assert "quando" in reminders.add("teste").lower()

def test_reminder_vencido_vai_pra_fila(monkeypatch, tmp_path):
    import reminders
    monkeypatch.setattr(reminders, "FILE", tmp_path / "l3.json")
    reminders._due_queue.clear()
    reminders.add("ja venceu", minutos=-1)   # já no passado
    # roda uma checagem manual (sem o loop)
    import json
    from datetime import datetime
    items = json.loads((tmp_path / "l3.json").read_text(encoding="utf-8"))
    for it in items:
        if datetime.fromisoformat(it["due"]) <= datetime.now():
            it["done"] = True
            reminders._due_queue.append({"text": it["text"]})
    due = reminders.pop_due()
    assert any("ja venceu" in d["text"] for d in due)


# ── app_launcher (sem abrir nada de verdade) ──
def test_open_app_conhecido(monkeypatch):
    import app_launcher
    chamadas = []
    monkeypatch.setattr("subprocess.Popen", lambda *a, **k: chamadas.append(a))
    r = app_launcher.open_app("calculadora")
    assert r["status"] == "ok" and chamadas

def test_open_site_normaliza_url(monkeypatch):
    import app_launcher
    cap = {}
    monkeypatch.setattr("webbrowser.open", lambda u: cap.setdefault("u", u))
    app_launcher.open_site("github.com")
    assert cap["u"].startswith("https://github.com")

def test_google_search(monkeypatch):
    import app_launcher
    cap = {}
    monkeypatch.setattr("webbrowser.open", lambda u: cap.setdefault("u", u))
    app_launcher.google_search("bolo de cenoura")
    assert "google.com/search" in cap["u"] and "bolo" in cap["u"]


# ── integrations ──
def test_available_tem_chaves():
    import integrations
    a = integrations.available()
    for k in ("youtube", "telegram", "openweather", "spotify", "google", "canva"):
        assert k in a

def test_whatsapp_monta_link(monkeypatch):
    import integrations
    cap = {}
    monkeypatch.setattr("webbrowser.open", lambda u: cap.setdefault("u", u))
    integrations.whatsapp_send("5583999998888", "ola")
    assert "wa.me/5583999998888" in cap["u"]


# ── agent (tool-use) ──
def test_agent_tools_presentes():
    import agent
    nomes = {t["name"] for t in agent.TOOLS}
    for n in ("tocar_musica", "clima", "buscar_conhecimento", "abrir_app",
              "criar_lembrete", "hora_data", "enviar_whatsapp", "programar"):
        assert n in nomes

def test_agent_hora_data():
    import agent
    r = agent._exec_tool("hora_data", {})
    assert "senhor" in r and ":" in r

def test_agent_lembrar_fato(monkeypatch, tmp_path):
    import agent, profile
    monkeypatch.setattr(profile, "PROFILE_FILE", tmp_path / "p.json")
    r = agent._exec_tool("lembrar_fato", {"fato": "uso GTX 1650"})
    assert "GTX 1650" in r


# ── knowledge (RAG) — funções puras ──
def test_knowledge_chunks():
    import knowledge
    texto = "a" * 500 + "\n\n" + "b" * 500
    chunks = knowledge._chunks(texto)
    assert len(chunks) >= 2

def test_knowledge_cosine():
    import knowledge
    assert abs(knowledge._cosine([1, 0], [1, 0]) - 1.0) < 1e-6
    assert abs(knowledge._cosine([1, 0], [0, 1])) < 1e-6
    assert knowledge._cosine([], []) == 0.0
