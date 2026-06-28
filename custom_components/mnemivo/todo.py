from __future__ import annotations

from typing import Any

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_LIST_IDS
from .coordinator import MnemivoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MnemivoCoordinator = hass.data[DOMAIN][entry.entry_id]
    lists = await coordinator.fetch_lists()
    list_map = {lst["id"]: lst["name"] for lst in lists}

    async_add_entities(
        MnemivoTodoList(coordinator, list_id, list_map.get(list_id, list_id))
        for list_id in entry.data[CONF_LIST_IDS]
    )


class MnemivoTodoList(CoordinatorEntity[MnemivoCoordinator], TodoListEntity):
    _attr_has_entity_name = True
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(
        self,
        coordinator: MnemivoCoordinator,
        list_id: str,
        list_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._list_id = list_id
        self._attr_name = list_name
        self._attr_unique_id = f"mnemivo_{list_id}"

    @property
    def todo_items(self) -> list[TodoItem]:
        rows = self.coordinator.data.get(self._list_id, [])
        return [
            TodoItem(
                uid=row["id"],
                summary=row["display_name"],
                status=(
                    TodoItemStatus.COMPLETE
                    if row.get("checked")
                    else TodoItemStatus.NEEDS_ACTION
                ),
                description=row.get("notes"),
            )
            for row in rows
        ]

    async def async_create_todo_item(self, item: TodoItem) -> None:
        created = await self.coordinator.async_create_item(
            self._list_id, item.summary or ""
        )
        # Optimistic update so HA reflects the new item immediately
        rows = list(self.coordinator.data.get(self._list_id, []))
        rows.append(created)
        self.coordinator.data[self._list_id] = rows
        self.async_write_ha_state()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        kwargs: dict[str, Any] = {}
        if item.status is not None:
            kwargs["checked"] = item.status == TodoItemStatus.COMPLETE
        if item.summary is not None:
            kwargs["summary"] = item.summary
        if not kwargs:
            return

        await self.coordinator.async_update_item(item.uid, **kwargs)

        # Optimistic update
        rows = list(self.coordinator.data.get(self._list_id, []))
        for i, row in enumerate(rows):
            if row["id"] == item.uid:
                rows[i] = {
                    **row,
                    "checked": kwargs.get("checked", row.get("checked", False)),
                    "display_name": kwargs.get("summary", row["display_name"]),
                }
                break
        self.coordinator.data[self._list_id] = rows
        self.async_write_ha_state()

    async def async_delete_todo_item(self, uids: list[str]) -> None:
        for uid in uids:
            await self.coordinator.async_delete_item(uid)

        # Optimistic update
        rows = self.coordinator.data.get(self._list_id, [])
        self.coordinator.data[self._list_id] = [
            r for r in rows if r["id"] not in uids
        ]
        self.async_write_ha_state()
