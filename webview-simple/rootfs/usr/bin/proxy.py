#!/usr/bin/env python3
"""
WebView Proxy – Home Assistant Addon (simpel)
Ruft eine externe URL ab und liefert sie selbst aus, damit keine
X-Frame-Options oder Content-Security-Policy den iframe blockiert.
"""

import asyncio, json, re, logging
from urllib.parse import urljoin, urlparse, quote, unquote
import aiohttp
from aiohttp import web
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# ── Konfiguration laden ───────────────────────────────────────────────────────
with open("/data/options.json") as f:
    cfg = json.load(f)

TARGET_URL = cfg.get("url", "https://example.com")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "de-DE,de;q=0.9",
    "Accept-Encoding": "identity",
}

# ── URL-Umschreiber ───────────────────────────────────────────────────────────
def proxify(url: str, base: str) -> str:
    """Wandelt eine absolute oder relative URL in eine Proxy-URL um."""
    if not url or url.startswith(("data:", "javascript:", "#")):
        return url
    parsed = urlparse(base)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if url.startswith("//"):   url = parsed.scheme + ":" + url
    elif url.startswith("/"):  url = origin + url
    elif not url.startswith("http"): url = urljoin(base, url)
    return "/r?u=" + quote(url, safe="")

def rewrite(html: str, base: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    parsed = urlparse(base)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    for t in soup.find_all("a",      href=True):  t["href"] = proxify(t["href"], base); t["target"] = "_self"
    for t in soup.find_all("link",   href=True):  t["href"] = proxify(t["href"], base)
    for t in soup.find_all("script", src=True):   t["src"]  = proxify(t["src"],  base)
    for t in soup.find_all("img",    src=True):   t["src"]  = proxify(t["src"],  base)
    for t in soup.find_all("source", src=True):   t["src"]  = proxify(t["src"],  base)

    # CSS url(...) in style-Attributen und <style>-Tags
    def fix_css(css):
        def rep(m):
            u = m.group(1).strip("'\"")
            return f"url('{proxify(u, base)}')"
        return re.sub(r"url\(([^)]+)\)", rep, css)

    for t in soup.find_all(style=True): t["style"] = fix_css(t["style"])
    for t in soup.find_all("style"):
        if t.string: t.string = fix_css(t.string)

    return str(soup)

# ── HTTP-Handlers ─────────────────────────────────────────────────────────────
async def handle_page(request: web.Request) -> web.Response:
    """Liefert die Hauptseite (Target-URL) als Proxy aus."""
    url = TARGET_URL
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15),
                             allow_redirects=True, ssl=False) as resp:
                ct = resp.content_type
                body = await resp.read()
                final_url = str(resp.url)
        except Exception as e:
            return web.Response(text=f"<h2>Fehler: {e}</h2>", content_type="text/html")

    if "text/html" in ct:
        html = body.decode("utf-8", errors="replace")
        html = rewrite(html, final_url)
        return web.Response(text=html, content_type="text/html", charset="utf-8")
    return web.Response(body=body, content_type=ct)


async def handle_resource(request: web.Request) -> web.Response:
    """Proxy für alle verlinkten Ressourcen (CSS, JS, Bilder…)."""
    url = unquote(request.query.get("u", ""))
    if not url:
        return web.Response(status=400)
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10),
                             allow_redirects=True, ssl=False) as resp:
                ct = resp.content_type or "application/octet-stream"
                body = await resp.read()
                if "text/css" in ct:
                    css = body.decode("utf-8", errors="replace")
                    css = re.sub(r"url\(([^)]+)\)", lambda m: "url('/r?u=" + quote(m.group(1).strip("'\""), safe="") + "')", css)
                    body = css.encode()
                return web.Response(body=body, content_type=ct)
        except Exception:
            return web.Response(status=502)


app = web.Application()
app.router.add_get("/",   handle_page)
app.router.add_get("/r",  handle_resource)

logging.info(f"WebView Proxy gestartet → {TARGET_URL} (Port 8099)")
web.run_app(app, host="0.0.0.0", port=8099, access_log=None)
