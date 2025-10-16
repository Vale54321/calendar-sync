import os, hashlib, time
from typing import Optional
from fastapi import FastAPI, Response, Header
import httpx

UPSTREAM_URL = os.environ.get("UPSTREAM_ICS_URL")
if not UPSTREAM_URL:
    raise RuntimeError("Setze die Umgebungsvariable UPSTREAM_ICS_URL auf die Hochschul-URL.")

FETCH_TIMEOUT = float(os.environ.get("FETCH_TIMEOUT", "15"))
CACHE_TTL = int(os.environ.get("CACHE_TTL_SECONDS", "300"))  # 5 min

app = FastAPI()
_cache = {
    "body": None,              # bytes
    "etag": None,              # str
    "last_modified": None,     # str
    "fetched_at": 0.0,         # float
}

def _normalize_ics(body: bytes) -> bytes:
    # auf UTF-8 und CRLF normalisieren
    text = body.decode("utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    return text.encode("utf-8")

async def _fetch_upstream() -> None:
    global _cache
    headers = {
        "Accept": "text/calendar, */*;q=0.1",
        "User-Agent": "ICS-Proxy/1.0 (+compatible)",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=FETCH_TIMEOUT, verify=True) as client:
        r = await client.get(UPSTREAM_URL, headers=headers)
        r.raise_for_status()
        body = _normalize_ics(r.content)
        etag = hashlib.sha256(body).hexdigest()
        last_mod = r.headers.get("Last-Modified")
        _cache.update({
            "body": body,
            "etag": etag,
            "last_modified": last_mod,
            "fetched_at": time.time(),
        })

@app.get("/healthz")
async def healthz():
    return {"ok": True, "cached": _cache["body"] is not None}

@app.get("/calendar.ics")
async def calendar_ics(if_none_match: Optional[str] = Header(default=None)):
    now = time.time()
    if (_cache["body"] is None) or (now - _cache["fetched_at"] > CACHE_TTL):
        await _fetch_upstream()

    # Client-Caching
    if if_none_match and if_none_match.strip('"') == _cache["etag"]:
        return Response(status_code=304)

    headers = {
        "Content-Type": "text/calendar; charset=utf-8",
        "Content-Disposition": 'attachment; filename="hochschule.ics"',
        "Cache-Control": f"public, max-age={CACHE_TTL}",
        "ETag": f'"{_cache["etag"]}"',
    }
    if _cache["last_modified"]:
        headers["Last-Modified"] = _cache["last_modified"]

    return Response(content=_cache["body"], media_type="text/calendar; charset=utf-8", headers=headers)
