from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN, CONF_LIST_IDS


async def _fetch_lists(api_url: str, api_token: str) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{api_url.rstrip('/')}/lists",
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            resp.raise_for_status()
            return await resp.json()


class MnemivoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._api_url = ""
        self._api_token = ""
        self._available_lists: list[dict] = []

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                lists = await _fetch_lists(
                    user_input[CONF_API_URL], user_input[CONF_API_TOKEN]
                )
                self._api_url = user_input[CONF_API_URL]
                self._api_token = user_input[CONF_API_TOKEN]
                self._available_lists = lists
                return await self.async_step_lists()
            except aiohttp.ClientResponseError as exc:
                errors["base"] = (
                    "invalid_auth" if exc.status == 401 else "cannot_connect"
                )
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_URL): str,
                    vol.Required(CONF_API_TOKEN): str,
                }
            ),
            errors=errors,
        )

    async def async_step_lists(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="Mnemivo",
                data={
                    CONF_API_URL: self._api_url,
                    CONF_API_TOKEN: self._api_token,
                    CONF_LIST_IDS: user_input[CONF_LIST_IDS],
                },
            )

        return self.async_show_form(
            step_id="lists",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LIST_IDS): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=lst["id"], label=lst["name"]
                                )
                                for lst in self._available_lists
                            ],
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
        )
