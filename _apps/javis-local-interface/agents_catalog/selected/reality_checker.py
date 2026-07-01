"""Reality Checker — ativação mínima (validador READ-ONLY).
Permissões: can_execute=False, can_write_files=False, requires_approval=True.
Não altera runtime nem dados. Só verifica EVIDÊNCIA antes de aceitar um "pronto".
Uso: python reality_checker.py  (Python 3.11)
"""
import json
import urllib.request

CAN_EXECUTE = False
CAN_WRITE_FILES = False
REQUIRES_APPROVAL = True
BASE = "http://localhost:8000"


def _http(path):
    req = urllib.request.Request(BASE + path, method="GET")
    try:
        r = urllib.request.urlopen(req, timeout=6)
        return r.status, r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return None, str(e)


def check(claim, path, expect_status, expect_redirect_contains=None):
    code, loc = _http(path)
    ok = (code == expect_status)
    if ok and expect_redirect_contains:
        ok = expect_redirect_contains in (loc or "")
    return {"claim": claim, "path": path, "got": code, "loc": loc, "PASS": ok}


def validate_delivery():
    """Valida uma entrega JÁ FEITA: raiz oficial + telas legadas arquivadas."""
    checks = [
        check("/ redireciona para command-center", "/", 200, "command-center"),  # urllib segue 307
        check("/command-center responde", "/command-center/", 200),
        check("/classic arquivada (404)", "/classic", 404),
        check("/central arquivada (404)", "/central/", 404),
        check("/painel arquivada (404)", "/painel", 404),
        check("/vempassear fallback (200)", "/vempassear", 200),
    ]
    verdict = "ACEITO" if all(c["PASS"] for c in checks) else "REJEITADO — evidência não bate"
    return {"agent": "Reality Checker", "can_execute": CAN_EXECUTE,
            "verdict": verdict, "checks": checks}


if __name__ == "__main__":
    print(json.dumps(validate_delivery(), ensure_ascii=False, indent=2))
