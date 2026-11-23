#!/usr/bin/env python3
"""Pobiera nowe oferty pracy z OLX (Białystok) i Białystok Online.

Użycie:
  python3 job-watcher/fetch.py [--max-age-days 3] [--out job-watcher/nowe.json]

Wypisuje/zapisuje listę NOWYCH ofert (nieobecnych na liście widzianych) z pełnym opisem.
Lista widzianych: --seen-file (dokument meta/widziane z bazy strony, zapisany przez ArtifactData z out_dir).
--mark-seen dopisuje identyfikatory z nowe.json i zapisuje {"ids": [...]} do --seen-out (do wgrania z powrotem do bazy).
Tylko biblioteka standardowa Pythona.
"""
import argparse, datetime as dt, html, json, re, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEEN = HERE / "seen.json"
MAX_SEEN = 6000


def load_seen(path):
    """Czyta identyfikatory z pliku: lista, {"ids": [...]} lub dokument zapisany przez ArtifactData."""
    p = Path(path)
    if not p.exists():
        return []
    def find(o):
        if isinstance(o, dict):
            if isinstance(o.get("ids"), list): return o["ids"]
            for v in o.values():
                r = find(v)
                if r is not None: return r
        if isinstance(o, list) and all(isinstance(x, str) for x in o): return o
        return None
    return find(json.loads(p.read_text())) or []
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
TZ = dt.timezone(dt.timedelta(hours=1))


def get(url):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pl-PL,pl;q=0.9"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # sieć bywa kapryśna
            err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{url}: {err}")


def clean(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s or "", flags=re.S)
    s = re.sub(r"<br\s*/?>|</p>|</li>", "\n", s)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"[ \t\xa0]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s).strip()


# ---------------- OLX ----------------
def olx(pages=3):
    out = []
    for p in range(1, pages + 1):
        url = f"https://www.olx.pl/praca/bialystok/?search%5Border%5D=created_at%3Adesc&page={p}"
        s = get(url)
        m = re.search(r'window.__PRERENDERED_STATE__\s*=\s*("(?:[^"\\]|\\.)*")', s)
        if not m:
            print(f"[OLX] brak danych na stronie {p}", file=sys.stderr)
            break
        ads = json.loads(json.loads(m.group(1)))["listing"]["listing"]["ads"]
        for a in ads:
            sal = a.get("salary") or {}
            stawka = ""
            if sal:
                per = {"hourly": "/h", "monthly": "/mies.", "daily": "/dzień"}.get(sal.get("period"), "")
                lo, hi = sal.get("from"), sal.get("to")
                stawka = (f"{lo}–{hi}" if lo and hi and lo != hi else str(lo or hi or "")) + f" {sal.get('currencySymbol','zł')}{per}"
                if sal.get("negotiable"): stawka += " (do negocjacji)"
            loc = a.get("location") or {}
            out.append({
                "id": f"olx-{a['id']}",
                "zrodlo": "OLX",
                "tytul": a["title"].strip(),
                "url": a["url"],
                "miejsce": loc.get("pathName") or loc.get("cityName", ""),
                "stawka": stawka.strip(),
                "dodano": a.get("lastRefreshTime") or a.get("createdTime"),
                "parametry": {x["name"]: x["value"] for x in a.get("params", [])},
                "firma": (a.get("user") or {}).get("name", ""),
                "opis": clean(a.get("description", ""))[:6000],
            })
    return out


# ---------------- Białystok Online ----------------
BO = "https://www.bialystokonline.pl"

def bo(pages=2, known=frozenset()):
    links = []
    for p in range(1, pages + 1):
        s = get(f"{BO}/praca-oferty-pracy,ogloszenia,9,{p}.html")
        for href in re.findall(r'href="/?([^"/][^"]*,ogloszenie,(\d+),9,1\.html)"', s):
            if href not in links: links.append(href)
    out = []
    for href, num in links:
        oid = f"bo-{num}"
        if oid in known: continue
        try:
            s = get(f"{BO}/{href}")
        except RuntimeError as e:
            print(f"[BO] {e}", file=sys.stderr); continue
        tm = re.search(r"<title>(.*?), Praca: Oferty pracy", s, re.S)
        tytul = clean(tm.group(1)) if tm else href.split(",")[0].replace("-", " ")
        i = s.find('class="hdrline-hdrs"')
        body = clean(s[i:i + 40000]) if i > 0 else clean(s)
        # treść ogłoszenia kończy się na "dodane: RRRR-MM-DD gg:mm:ss"
        dm = re.search(r"dodane:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)
        j = body.find(tytul)
        opis = body[j:dm.start()] if (j >= 0 and dm) else body[:4000]
        sal = re.match(re.escape(tytul) + r"\s*([\d\s.,–-]+(?:zł)?)\s", opis)
        stawka = re.sub(r"\s*zł$", "", sal.group(1).strip()) + " zł" if sal and re.search(r"\d{3}", sal.group(1)) else ""
        after = body[dm.end():dm.end() + 300] if dm else ""
        mm = re.search(r"pokaż numer\s+([A-ZŁŚŻŹĆ][\wąćęłńóśźż .-]{1,40}?)(?:\s{2,}|\s+(?:Zobacz|Podobne|Inne|Ogłoszenia)|$)", after)
        out.append({
            "id": oid,
            "zrodlo": "Białystok Online",
            "tytul": tytul,
            "url": f"{BO}/{href}",
            "miejsce": (mm.group(1).strip() if mm else "Białystok"),
            "stawka": stawka,
            "dodano": (dm.group(1).replace(" ", "T") + "+01:00") if dm else "",
            "parametry": {},
            "firma": "",
            "opis": opis.strip()[:6000],
        })
        time.sleep(0.5)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-days", type=float, default=3, help="pomijaj oferty starsze niż tyle dni")
    ap.add_argument("--out", default=str(HERE / "nowe.json"))
    ap.add_argument("--seen-file", default=str(SEEN), help="plik z listą widzianych identyfikatorów")
    ap.add_argument("--seen-out", default=str(HERE / "widziane.json"), help="gdzie zapisać zaktualizowaną listę")
    ap.add_argument("--mark-seen", nargs="?", const=str(HERE / "nowe.json"),
                    help="dopisz identyfikatory z podanego pliku do listy widzianych i zakończ")
    a = ap.parse_args()

    seen_list = load_seen(a.seen_file)
    seen = set(seen_list)
    if a.mark_seen:
        new = [o["id"] for o in json.loads(Path(a.mark_seen).read_text()) if o["id"] not in seen]
        merged = (seen_list + new)[-MAX_SEEN:]
        Path(a.seen_out).write_text(json.dumps({"ids": merged}))
        print(f"widziane: +{len(new)} (razem {len(merged)}) -> {a.seen_out}")
        return

    cutoff = dt.datetime.now(TZ) - dt.timedelta(days=a.max_age_days)
    oferty, bledy = [], []
    for name, fn in (("OLX", lambda: olx()), ("Białystok Online", lambda: bo(known=frozenset(seen)))):
        try:
            oferty += fn()
        except Exception as e:
            bledy.append(f"{name}: {e}")
    nowe, ids = [], set()
    for o in oferty:
        if o["id"] in seen or o["id"] in ids: continue
        try:
            if o["dodano"] and dt.datetime.fromisoformat(o["dodano"]) < cutoff: continue
        except ValueError:
            pass
        ids.add(o["id"]); nowe.append(o)
    Path(a.out).write_text(json.dumps(nowe, ensure_ascii=False, indent=1))
    print(f"Nowe oferty: {len(nowe)} (OLX {sum(o['zrodlo']=='OLX' for o in nowe)}, "
          f"BO {sum(o['zrodlo']!='OLX' for o in nowe)}) -> {a.out}")
    for b in bledy: print("BŁĄD", b, file=sys.stderr)
    if bledy and not oferty: sys.exit(2)


if __name__ == "__main__":
    main()
