#!/usr/bin/env python3
"""
debug_json.py — Affiche le JSON brut de l'API TIBI
====================================================
Exécute une fois pour voir la structure exacte du JSON
retourné par /app.php?page=history&year=YYYY

Usage:
    pip install requests
    python debug_json.py
"""
import json
import sys

try:
    import requests
except ImportError:
    print("❌  pip install requests")
    sys.exit(1)

BASE_URL  = "https://tibi.monconteneur.be"
LOGIN_URL = f"{BASE_URL}/login"
HOME_URL  = f"{BASE_URL}/home"
API_URL   = f"{BASE_URL}/app.php"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) "
        "Gecko/20100101 Firefox/152.0"
    ),
    "Accept-Language": "fr,en-US;q=0.9",
}

def main():
    username = input("web_login (nom d'utilisateur TIBI) : ").strip()
    password = input("password                           : ").strip()
    year     = input("Année [2026]                       : ").strip() or "2026"

    session = requests.Session()
    session.headers.update(HEADERS)

    # 1. GET /login → PHPSESSID
    print(f"\n📡 GET {LOGIN_URL}")
    r = session.get(LOGIN_URL)
    print(f"   → {r.status_code}  cookies: {list(session.cookies.keys())}")

    # 2. POST /login
    print(f"📡 POST {LOGIN_URL}")
    r = session.post(
        LOGIN_URL,
        data={"web_login": username, "password": password, "remember": "on"},
        headers={
            "Content-Type":   "application/x-www-form-urlencoded",
            "Origin":         BASE_URL,
            "Referer":        LOGIN_URL,
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
        },
        allow_redirects=True,
    )
    print(f"   → {r.status_code}  URL finale: {r.url}")

    if "/login" in str(r.url):
        print("\n❌ Login échoué — vérifie tes identifiants")
        sys.exit(1)

    print("✅ Login OK !")

    # 3. GET /app.php?page=history&year=YYYY
    print(f"\n📡 GET {API_URL}?page=history&year={year}")
    r = session.get(
        API_URL,
        params={"page": "history", "year": year},
        headers={
            "Accept":           "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer":          HOME_URL,
            "Sec-Fetch-Dest":   "empty",
            "Sec-Fetch-Mode":   "cors",
            "Sec-Fetch-Site":   "same-origin",
        },
    )
    print(f"   → {r.status_code}  Content-Type: {r.headers.get('Content-Type', '?')}")

    # Affiche le JSON brut formaté
    print("\n" + "="*60)
    print("  JSON BRUT REÇU")
    print("="*60)
    try:
        data = r.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print("⚠️  Pas du JSON — réponse brute :")
        print(r.text[:2000])

    print("\n" + "="*60)
    print("Copie ce JSON et partage-le pour affiner le parseur.")
    print("="*60)

if __name__ == "__main__":
    main()
