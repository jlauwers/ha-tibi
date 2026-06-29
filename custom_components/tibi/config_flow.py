"""Config flow pour l'intégration TIBI (interface graphique HA)."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOGIN_URL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=300, max=86400)
        ),
    }
)


async def _test_credentials(username: str, password: str) -> bool:
    """Teste les identifiants TIBI. Retourne True si OK."""
    connector = aiohttp.TCPConnector(ssl=True)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) "
            "Gecko/20100101 Firefox/152.0 AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr,en-US;q=0.9,en;q=0.8",
    }
    async with aiohttp.ClientSession(
        connector=connector,
        headers=headers,
        cookie_jar=aiohttp.CookieJar(),
    ) as session:
        # GET /login pour poser le PHPSESSID
        try:
            async with session.get(LOGIN_URL) as resp:
                await resp.text()
        except aiohttp.ClientError:
            return False

        # POST avec les vrais noms de champs (confirmés via DevTools)
        payload = {
            "web_login": username,
            "password":  password,
            "remember":  "on",
        }
        post_headers = {
            "Content-Type":   "application/x-www-form-urlencoded",
            "Origin":         BASE_URL,
            "Referer":        LOGIN_URL,
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }

        try:
            async with session.post(
                LOGIN_URL,
                data=payload,
                headers=post_headers,
                allow_redirects=True,
            ) as resp:
                resp_text = await resp.text()
                final_url = str(resp.url)
        except aiohttp.ClientError:
            return False

        return (
            "/login" not in final_url
            or "logout" in resp_text.lower()
            or "déconnexion" in resp_text.lower()
            or "statistiques" in resp_text.lower()
            or "production de déchets" in resp_text.lower()
        )


class TibiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestion du flux de configuration TIBI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape initiale : saisie identifiants."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            try:
                valid = await _test_credentials(username, password)
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                if valid:
                    await self.async_set_unique_id(f"tibi_{username}")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"TIBI ({username})",
                        data={
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                            CONF_SCAN_INTERVAL: user_input.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            ),
                        },
                    )
                else:
                    errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "url": "https://tibi.monconteneur.be",
            },
        )
