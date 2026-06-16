# vp_store.py — armazenamento local (JSON) do painel Vem Passear.
# Espelha o padrão de history_store.py: simples, sem banco, persistente entre sessões.
import json
from pathlib import Path
from datetime import datetime

_DATA_DIR   = Path(__file__).parent.parent / "_data"
_PASSEIOS   = _DATA_DIR / "vp_passeios.json"
_CLIENTES   = _DATA_DIR / "vp_clientes.json"
_CONTEUDOS  = _DATA_DIR / "vp_conteudos.json"
_PAUTA      = _DATA_DIR / "vp_pauta.json"


def _read(file: Path) -> list[dict]:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not file.exists():
        return []
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write(file: Path, data: list[dict]) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _new_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


# ── Passeios ──────────────────────────────────────────────────────────
def list_passeios() -> list[dict]:
    """Passeios ordenados por data (mais próximos primeiro)."""
    return sorted(_read(_PASSEIOS), key=lambda p: p.get("data", ""))


def add_passeio(tipo: str, data: str, pessoas: int, valor: float) -> dict:
    passeios = _read(_PASSEIOS)
    item = {
        "id": _new_id(),
        "tipo": tipo,
        "data": data,
        "pessoas": int(pessoas),
        "valor": float(valor),
        "ts": datetime.now().isoformat(),
    }
    passeios.append(item)
    _write(_PASSEIOS, passeios)
    return item


def remove_passeio(item_id: str) -> bool:
    passeios = _read(_PASSEIOS)
    novos = [p for p in passeios if p.get("id") != item_id]
    if len(novos) == len(passeios):
        return False
    _write(_PASSEIOS, novos)
    return True


def passeios_resumo() -> dict:
    passeios = _read(_PASSEIOS)
    return {
        "total_passeios": len(passeios),
        "total_pessoas": sum(p.get("pessoas", 0) for p in passeios),
        "faturamento": round(sum(p.get("valor", 0) * p.get("pessoas", 0) for p in passeios), 2),
    }


# ── Clientes / Leads ──────────────────────────────────────────────────
def list_clientes() -> dict:
    """Separa em leads e fechados."""
    todos = _read(_CLIENTES)
    return {
        "leads":    [c for c in todos if c.get("status") != "fechado"],
        "fechados": [c for c in todos if c.get("status") == "fechado"],
    }


def add_cliente(nome: str, contato: str = "", obs: str = "") -> dict:
    clientes = _read(_CLIENTES)
    item = {
        "id": _new_id(),
        "nome": nome,
        "contato": contato,
        "obs": obs,
        "status": "lead",
        "ts": datetime.now().isoformat(),
    }
    clientes.append(item)
    _write(_CLIENTES, clientes)
    return item


def set_status(item_id: str, status: str) -> bool:
    clientes = _read(_CLIENTES)
    achou = False
    for c in clientes:
        if c.get("id") == item_id:
            c["status"] = status
            achou = True
            break
    if achou:
        _write(_CLIENTES, clientes)
    return achou


def remove_cliente(item_id: str) -> bool:
    clientes = _read(_CLIENTES)
    novos = [c for c in clientes if c.get("id") != item_id]
    if len(novos) == len(clientes):
        return False
    _write(_CLIENTES, novos)
    return True


# ── Biblioteca de Conteúdo (textos gerados, salvos pra reusar) ────────
def list_conteudos() -> list[dict]:
    """Mais recentes primeiro."""
    return list(reversed(_read(_CONTEUDOS)))


def add_conteudo(tipo: str, texto: str) -> dict:
    conteudos = _read(_CONTEUDOS)
    item = {
        "id": _new_id(),
        "tipo": tipo,
        "texto": texto,
        "ts": datetime.now().isoformat(),
    }
    conteudos.append(item)
    _write(_CONTEUDOS, conteudos[-100:])
    return item


def remove_conteudo(item_id: str) -> bool:
    conteudos = _read(_CONTEUDOS)
    novos = [c for c in conteudos if c.get("id") != item_id]
    if len(novos) == len(conteudos):
        return False
    _write(_CONTEUDOS, novos)
    return True


# ── Linha Editorial (pauta de posts planejados) ──────────────────────
def list_pauta() -> list[dict]:
    """Ordenado por data."""
    return sorted(_read(_PAUTA), key=lambda p: p.get("data", ""))


def add_pauta(data: str, canal: str, ideia: str) -> dict:
    pauta = _read(_PAUTA)
    item = {
        "id": _new_id(),
        "data": data,
        "canal": canal,
        "ideia": ideia,
        "status": "planejado",
        "ts": datetime.now().isoformat(),
    }
    pauta.append(item)
    _write(_PAUTA, pauta)
    return item


def set_pauta_status(item_id: str, status: str) -> bool:
    pauta = _read(_PAUTA)
    achou = False
    for p in pauta:
        if p.get("id") == item_id:
            p["status"] = status
            achou = True
            break
    if achou:
        _write(_PAUTA, pauta)
    return achou


def remove_pauta(item_id: str) -> bool:
    pauta = _read(_PAUTA)
    novos = [p for p in pauta if p.get("id") != item_id]
    if len(novos) == len(pauta):
        return False
    _write(_PAUTA, novos)
    return True
