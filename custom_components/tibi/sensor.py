"""Sensors Home Assistant pour les quotas TIBI."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ADDRESS,
    ATTR_HOUSEHOLD,
    ATTR_LAST_DATE,
    ATTR_LAST_KG,
    ATTR_NR_PUCE,
    ATTR_STATUS,
    ATTR_YEAR,
    DOMAIN,
    FRACTION_ORGANIQUE,
    FRACTION_TOUT_VENANT,
    UNIT_COLLECTIONS,
    UNIT_KG,
)
from .coordinator import TibiCoordinator


@dataclass(frozen=True)
class TibiSensorEntityDescription(SensorEntityDescription):
    """Description étendue pour les sensors TIBI."""

    fraction: str = ""
    value_key: str = ""


SENSOR_TYPES: tuple[TibiSensorEntityDescription, ...] = (
    # ── Tout Venant ───────────────────────────────────────────────────
    TibiSensorEntityDescription(
        key="tv_vidanges",
        name="Tout Venant – Levées",
        icon="mdi:trash-can-outline",
        native_unit_of_measurement=UNIT_COLLECTIONS,
        state_class=SensorStateClass.TOTAL,          # TOTAL + last_reset gère le reset annuel
        fraction=FRACTION_TOUT_VENANT,
        value_key="total_vidanges",
    ),
    TibiSensorEntityDescription(
        key="tv_kilos",
        name="Tout Venant – Kilos",
        icon="mdi:weight-kilogram",
        native_unit_of_measurement=UNIT_KG,
        state_class=SensorStateClass.TOTAL,
        fraction=FRACTION_TOUT_VENANT,
        value_key="total_kilos",
    ),
    # ── Organique ────────────────────────────────────────────────────
    TibiSensorEntityDescription(
        key="org_vidanges",
        name="Organique – Levées",
        icon="mdi:leaf",
        native_unit_of_measurement=UNIT_COLLECTIONS,
        state_class=SensorStateClass.TOTAL,
        fraction=FRACTION_ORGANIQUE,
        value_key="total_vidanges",
    ),
    TibiSensorEntityDescription(
        key="org_kilos",
        name="Organique – Kilos",
        icon="mdi:weight-kilogram",
        native_unit_of_measurement=UNIT_KG,
        state_class=SensorStateClass.TOTAL,
        fraction=FRACTION_ORGANIQUE,
        value_key="total_kilos",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Créé les entités sensor TIBI."""
    coordinator: TibiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TibiSensor(coordinator, description) for description in SENSOR_TYPES
    )


class TibiSensor(CoordinatorEntity[TibiCoordinator], SensorEntity):
    """Sensor représentant une métrique TIBI."""

    entity_description: TibiSensorEntityDescription

    def __init__(
        self,
        coordinator: TibiCoordinator,
        description: TibiSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"tibi_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "tibi_conteneurs")},
            "name": "TIBI Conteneurs",
            "manufacturer": "TIBI",
            "model": "Quotas conteneurs à puce",
            "entry_type": "service",
        }

    @property
    def last_reset(self) -> datetime:
        """
        Retourne le 1er janvier de l'année en cours (timezone-aware).
        HA utilise cette valeur pour détecter les resets annuels
        sans générer d'erreurs quand les compteurs repassent à 0.
        """
        now = datetime.now(tz=timezone.utc)
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    @property
    def native_value(self) -> float | int | None:
        """Valeur principale du sensor."""
        if not self.coordinator.data:
            return None
        fraction_data = self.coordinator.data.get("fractions", {}).get(
            self.entity_description.fraction
        )
        if not fraction_data:
            return None
        return fraction_data.get(self.entity_description.value_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Attributs supplémentaires exposés dans HA."""
        attrs: dict[str, Any] = {}
        if not self.coordinator.data:
            return attrs

        data          = self.coordinator.data
        fraction_data = data.get("fractions", {}).get(self.entity_description.fraction)

        if fraction_data:
            attrs[ATTR_STATUS]  = fraction_data.get("statut")
            attrs[ATTR_NR_PUCE] = fraction_data.get("nr_puce")
            attrs["depuis"]     = fraction_data.get("depuis")

            collections = fraction_data.get("collections", [])
            if collections:
                last = collections[-1]
                attrs[ATTR_LAST_DATE] = last.get("date")
                attrs[ATTR_LAST_KG]   = last.get("kilos")
                attrs["collectes"]    = [
                    {"date": c["date"], "kg": c["kilos"]} for c in collections
                ]

        attrs[ATTR_YEAR]      = data.get("year")
        attrs[ATTR_HOUSEHOLD] = data.get("household")
        attrs[ATTR_ADDRESS]   = data.get("address")
        attrs["actif_depuis"] = data.get("since")

        return attrs
