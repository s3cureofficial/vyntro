"""Aktuelle Nachrichten zu einem Wert: deutsche Artikel über Google News (RSS)
und englische Finanznachrichten über Yahoo Finance."""

from __future__ import annotations

import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests
import yfinance as yf

ZUSAETZE = re.compile(
    r",?\s+(Inc\.?|Corporation|Corp\.?|AG|SE|N\.V\.|plc|PLC|Ltd\.?|Holdings?|Co\.|"
    r"Company|Group|S\.A\.|USD|EUR|UCITS.*|ETF.*|\(.*\))$")


def suchname(name: str, typ: str) -> str:
    """Kurzer Name für die Suche, z. B. 'SoFi Technologies, Inc.' -> 'SoFi Technologies'."""
    n = name
    for _ in range(4):
        n2 = ZUSAETZE.sub("", n).strip(" ,")
        if n2 == n or not n2:
            break
        n = n2
    n = " ".join(n.split()[:4])
    if typ == "Krypto":
        return f"{n} Kurs"
    if typ == "ETF":
        return f"{n} ETF"
    return f"{n} Aktie"


def _google(query: str, anzahl: int) -> list[dict]:
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": f"{query} when:14d", "hl": "de", "gl": "DE", "ceid": "DE:de"})
    r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    out = []
    for it in ET.fromstring(r.content).findall("./channel/item")[:anzahl * 2]:
        quelle = it.findtext("source") or ""
        titel = it.findtext("title") or ""
        if quelle and titel.endswith(" - " + quelle):
            titel = titel[: -len(quelle) - 3]
        try:
            zeit = parsedate_to_datetime(it.findtext("pubDate"))
        except Exception:  # noqa: BLE001
            continue
        out.append({"titel": titel.strip(), "quelle": quelle, "zeit": zeit,
                    "link": it.findtext("link") or "", "sprache": "DE"})
    return out


def _yahoo(ticker: str, anzahl: int) -> list[dict]:
    out = []
    passend = {ticker.upper(), ticker.split(".")[0].upper()}
    for kandidat in dict.fromkeys([ticker, ticker.split(".")[0]]):
        for n in yf.Search(kandidat, max_results=1, news_count=anzahl).news:
            if not n.get("title") or not n.get("providerPublishTime"):
                continue
            if not passend & {t.upper() for t in n.get("relatedTickers") or []}:
                continue  # Artikel betrifft den Wert nicht direkt
            out.append({"titel": n["title"], "quelle": n.get("publisher", ""),
                        "zeit": datetime.fromtimestamp(n["providerPublishTime"], timezone.utc),
                        "link": n.get("link", ""), "sprache": "EN"})
        if out:
            break
    return out


def hole(ticker: str, name: str, typ: str, anzahl: int = 10) -> list[dict]:
    artikel = []
    for quelle in (lambda: _google(suchname(name, typ), anzahl),
                   lambda: _yahoo(ticker, anzahl)):
        try:
            artikel += quelle()
        except Exception:  # noqa: BLE001
            pass
    gesehen, eindeutig = set(), []
    for a in sorted(artikel, key=lambda a: a["zeit"], reverse=True):
        schluessel = a["titel"].lower()[:60]
        if schluessel not in gesehen:
            gesehen.add(schluessel)
            eindeutig.append(a)
    return eindeutig[:anzahl]


def vor_wann(zeit: datetime) -> str:
    sek = (datetime.now(timezone.utc) - zeit).total_seconds()
    if sek < 3600:
        return f"vor {max(1, int(sek // 60))} Min."
    if sek < 86400:
        return f"vor {int(sek // 3600)} Std."
    tage = int(sek // 86400)
    return "gestern" if tage == 1 else f"vor {tage} Tagen"
