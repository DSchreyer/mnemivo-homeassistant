from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_API_URL, CONF_API_TOKEN, CONF_LIST_IDS, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class MnemivoCoordinator(DataUpdateCoordinator[dict[str, list[dict]]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api_url = entry.data[CONF_API_URL].rstrip("/")
        self.api_token = entry.data[CONF_API_TOKEN]
        self.list_ids: list[str] = entry.data[CONF_LIST_IDS]

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def _async_update_data(self) -> dict[str, list[dict]]:
        data: dict[str, list[dict]] = {}
        try:
            async with aiohttp.ClientSession() as session:
                for list_id in self.list_ids:
                    async with session.get(
                        f"{self.api_url}/lists/{list_id}/items",
                        headers=self._headers(),
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        resp.raise_for_status()
                        data[list_id] = await resp.json()
        except aiohttp.ClientResponseError as exc:
            raise UpdateFailed(f"HTTP {exc.status}: {exc.message}") from exc
        except Exception as exc:
            raise UpdateFailed(f"Error fetching Mnemivo data: {exc}") from exc
        return data

    async def fetch_lists(self) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/lists",
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def async_create_item(self, list_id: str, summary: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/lists/{list_id}/items",
                headers=self._headers(),
                json={"summary": summary},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def async_update_item(self, item_id: str, **kwargs: object) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.api_url}/items/{item_id}",
                headers=self._headers(),
                json=kwargs,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()

    async def async_delete_item(self, item_id: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.api_url}/items/{item_id}",
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
