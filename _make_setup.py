import json
from pathlib import Path
from urllib.request import Request, urlopen

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent
vals = dotenv_values(ROOT / ".env")
token = (vals.get("MAKE_TOKENS") or "").strip()
ua = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)
SCENARIO_ID = 7983749


def call(method: str, path: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode()
    req = Request("https://eu1.make.com/api/v2" + path, data=data, method=method)
    req.add_header("Authorization", "Token " + token)
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", ua)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8", "replace")
            print("OK", method, path, resp.status)
            parsed = json.loads(body) if body else {}
            print(json.dumps(parsed, ensure_ascii=False)[:2500])
            return parsed
    except Exception as exc:
        err = ""
        if hasattr(exc, "read"):
            err = exc.read()[:3000].decode("utf-8", "replace")
        print(
            "ERR",
            method,
            path,
            getattr(exc, "code", type(exc).__name__),
            err[:3000] or str(exc)[:800],
        )
        return None


for method, path, payload in (
    ("POST", f"/scenarios/{SCENARIO_ID}/start", None),
    ("POST", f"/scenarios/{SCENARIO_ID}/activate", None),
    ("PATCH", f"/scenarios/{SCENARIO_ID}", {"islinked": True}),
):
    print("--- try", method, path, "---")
    result = call(method, path, payload)
    if result is not None:
        break
