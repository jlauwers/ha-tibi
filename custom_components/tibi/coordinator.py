"""Coordinator TIBI : login PHP + API JSON /app.php?page=history&year=YYYY.

Structure JSON confirmée via debug_json.py :

  { "history": [ {
      "resident_count": "6",
      "since": "29/06/2018",
      "card": {
        "street": "...", "city": "...", "zip": "...", "nr": "...",
        "products": [
          {
            "chip":         "4000000D0034FD",   # null si inactif
            "chip_trimmed": "4000000D0034FD",
            "status":       "active",           # ou "inactive"
            "state":        "active",
            "status_since": "2020-02-05",
            "fraction":     "REST",             # REST = Tout Venant, GFT = Organique
            "emptyings": {
              "2026-01-05": { "date_time":"2026-01-05", "weight":"28.00", "amount":1 },
              ...
            }
          }, ...
        ]
      }
  } ] }

Notes :
  - vidanges = len(emptyings)  (nombre de dates distinctes, confirmé vs UI)
  - kilos    = sum(weight)     (weight peut être str ou int)
  - Ignorer les produits avec status/state != "active"
  - "REST" → TOUT VENANT  |  "GFT" → ORGANIQUE
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_URL,
    BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FRACTION_ORGANIQUE,
    FRACTION_TOUT_VENANT,
    HOME_URL,
    LOGIN_URL,
)

_LOGGER = logging.getLogger(__name__)

# Correspondance fraction JSON → constante HA
FRACTION_MAP: dict[str, str] = {
    "REST": FRACTION_TOUT_VENANT,  # restafval = tout venant
    "GFT":  FRACTION_ORGANIQUE,    # groente/fruit/tuin = organique
}

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) "
        "Gecko/20100101 Firefox/152.0 AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Cache-Control":   "no-cache",
    "Pragma":          "no-cache",
}


class TibiCoordinator(DataUpdateCoordinator):
    """Coordinateur pour les données TIBI."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.username    = username
        self.password    = password
        self._session: aiohttp.ClientSession | None = None
        self._logged_in  = False

    # ------------------------------------------------------------------ #
    #  Session                                                             #
    # ------------------------------------------------------------------ #

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=True),
                headers=DEFAULT_HEADERS,
                cookie_jar=aiohttp.CookieJar(),
            )
            self._logged_in = False
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    # ------------------------------------------------------------------ #
    #  Login                                                               #
    # ------------------------------------------------------------------ #

    async def _login(self) -> bool:
        """
        Séquence confirmée via DevTools :
          GET  /login  →  pose PHPSESSID
          POST /login  →  web_login + password + remember=on  →  302
          GET  /home   →  page authentifiée
        """
        session = await self._get_session()

        # 1. GET /login — initialise le cookie PHPSESSID
        try:
            async with session.get(
                LOGIN_URL,
                headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
                allow_redirects=True,
            ) as resp:
                await resp.read()
        except aiohttp.ClientError as err:
            _LOGGER.error("GET /login échoué: %s", err)
            return False

        # 2. POST /login — champs confirmés via curl DevTools
        try:
            async with session.post(
                LOGIN_URL,
                data={
                    "web_login": self.username,
                    "password":  self.password,
                    "remember":  "on",
                },
                headers={
                    "Content-Type":   "application/x-www-form-urlencoded",
                    "Accept":         "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Origin":         BASE_URL,
                    "Referer":        LOGIN_URL,
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-User": "?1",
                },
                allow_redirects=True,  # suit le 302 → /home
            ) as resp:
                final_url = str(resp.url)
                await resp.read()
        except aiohttp.ClientError as err:
            _LOGGER.error("POST /login échoué: %s", err)
            return False

        self._logged_in = "/login" not in final_url
        if self._logged_in:
            _LOGGER.info("✅ Login TIBI réussi")
        else:
            _LOGGER.warning("❌ Login TIBI échoué (toujours sur /login)")
        return self._logged_in

    # ------------------------------------------------------------------ #
    #  Appel API JSON                                                      #
    # ------------------------------------------------------------------ #

    async def _fetch_history(self, year: int) -> dict:
        """GET /app.php?page=history&year=YYYY  (XHR jQuery, retourne JSON)."""
        session = await self._get_session()

        try:
            async with session.get(
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
                allow_redirects=False,
            ) as resp:
                # Session expirée → redirect vers /login
                if resp.status in (301, 302, 303):
                    _LOGGER.info("Session TIBI expirée, re-login…")
                    self._logged_in = False
                    if not await self._login():
                        raise UpdateFailed("Re-login TIBI échoué")
                    return await self._fetch_history(year)

                if resp.status != 200:
                    raise UpdateFailed(f"API TIBI HTTP {resp.status}")

                payload = await resp.json(content_type=None)
                if payload.get("error"):
                    _LOGGER.warning("API TIBI erreur: %s", payload["error"])
                return payload

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Réseau TIBI: {err}") from err

    # ------------------------------------------------------------------ #
    #  Parsing JSON — structure exacte confirmée                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse(raw: dict, year: int) -> dict[str, Any]:
        """
        Parse la réponse de /app.php?page=history&year=YYYY.

        Règles confirmées :
          - vidanges  = len(product.emptyings)   # nb de dates distinctes
          - kilos     = sum(e["weight"])          # weight est str ou int
          - Ignorer   products avec state != "active"
          - REST → TOUT VENANT  |  GFT → ORGANIQUE
        """
        result: dict[str, Any] = {
            "year":      year,
            "fractions": {
                FRACTION_TOUT_VENANT: _empty_fraction(FRACTION_TOUT_VENANT),
                FRACTION_ORGANIQUE:   _empty_fraction(FRACTION_ORGANIQUE),
            },
            "household": None,
            "address":   None,
            "name":      None,
            "since":     None,
        }

        history = raw.get("history") or []
        if not history:
            _LOGGER.warning("Réponse TIBI : champ 'history' vide")
            return result

        # On prend le premier titulaire (usage résidentiel = toujours 1)
        entry = history[0]

        result["since"] = entry.get("since")

        hh = entry.get("resident_count")
        if hh is not None:
            try:
                result["household"] = int(hh)
            except (ValueError, TypeError):
                result["household"] = hh

        card = entry.get("card") or {}
        street = card.get("street", "")
        nr     = card.get("nr",     "")
        zp     = card.get("zip",    "")
        city   = card.get("city",   "")
        result["address"] = f"{street} {nr}, {zp} {city}".strip()

        # ── Produits (conteneurs) ──────────────────────────────────────
        # Un ménage peut avoir plusieurs conteneurs actifs de même fraction
        # (ex: déménagement partiel, remplacement de puce).
        # On accumule toutes les collectes au lieu d'écraser.
        products = card.get("products") or []
        for product in products:
            # Ignore les conteneurs inactifs
            if product.get("state") != "active":
                continue

            frac_raw = product.get("fraction", "")
            frac_key = FRACTION_MAP.get(frac_raw.upper())
            if frac_key is None:
                _LOGGER.debug("Fraction inconnue ignorée: %s", frac_raw)
                continue

            frac = result["fractions"][frac_key]

            # Infos puce : on garde la première puce active trouvée
            if frac["nr_puce"] is None:
                frac["nr_puce"] = product.get("chip_trimmed") or product.get("chip")
                frac["statut"]  = product.get("status") or product.get("state")
                frac["depuis"]  = product.get("status_since") or product.get("chip_since")

            emptyings = product.get("emptyings") or {}

            # emptyings est un dict {"YYYY-MM-DD": {date_time, weight, amount}}
            if isinstance(emptyings, dict) and emptyings:
                for date_key in sorted(emptyings.keys()):
                    e  = emptyings[date_key]
                    kg = _to_float(e.get("weight", 0))
                    # Fusionne les collectes du même jour si plusieurs conteneurs
                    existing = next(
                        (c for c in frac["collections"] if c["date"] == date_key), None
                    )
                    if existing:
                        existing["kilos"] = round(existing["kilos"] + kg, 2)
                    else:
                        frac["collections"].append({
                            "date":    date_key,
                            "vidanges": 1,
                            "kilos":   kg,
                        })

        # Tri et totaux après accumulation de tous les produits
        for frac in result["fractions"].values():
            frac["collections"].sort(key=lambda c: c["date"])
            frac["total_vidanges"] = len(frac["collections"])
            frac["total_kilos"]    = round(
                sum(c["kilos"] for c in frac["collections"]), 2
            )

        _LOGGER.debug("TIBI parsé: TV=%s vidanges / %s kg | OM=%s vidanges / %s kg",
                      result["fractions"][FRACTION_TOUT_VENANT]["total_vidanges"],
                      result["fractions"][FRACTION_TOUT_VENANT]["total_kilos"],
                      result["fractions"][FRACTION_ORGANIQUE]["total_vidanges"],
                      result["fractions"][FRACTION_ORGANIQUE]["total_kilos"])
        return result

    # ------------------------------------------------------------------ #
    #  Update HA                                                          #
    # ------------------------------------------------------------------ #

    async def _async_update_data(self) -> dict[str, Any]:
        if not self._logged_in:
            if not await self._login():
                raise UpdateFailed("Login TIBI échoué — vérifier identifiants")

        year = datetime.now().year
        raw  = await self._fetch_history(year)
        return self._parse(raw, year)


# ── Helpers ─────────────────────────────────────────────────────────────── #

def _empty_fraction(name: str) -> dict[str, Any]:
    return {
        "fraction":       name,
        "nr_puce":        None,
        "statut":         None,
        "depuis":         None,
        "collections":    [],
        "total_vidanges": 0,
        "total_kilos":    0.0,
    }


def _to_float(val: Any) -> float:
    """Convertit weight (str '28.00' ou int 43) en float."""
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, TypeError):
        return 0.0
