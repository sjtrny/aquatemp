from abc import ABC
import logging
import sys

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import ALL_ENTITIES, DOMAIN
from .common.entity_descriptions import AquaTempSelectEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the sensor platform."""
    try:
        coordinator = hass.data[DOMAIN][entry.entry_id]
        entities = []
        entity_descriptions = []

        for entity_description in ALL_ENTITIES:
            if entity_description.platform == Platform.SELECT:
                entity_descriptions.append(entity_description)

        for device_code in coordinator.api_data:
            for entity_description in entity_descriptions:
                entity = AquaTempSelectEntity(
                    device_code, entity_description, coordinator
                )

                entities.append(entity)

        _LOGGER.debug(f"Setting up sensor entities: {entities}")

        async_add_entities(entities, True)
    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"Failed to initialize select, Error: {ex}, Line: {line_number}")


class AquaTempSelectEntity(CoordinatorEntity, SelectEntity, ABC):
    """Representation of a sensor."""

    def __init__(
        self,
        device_code: str,
        entity_description: AquaTempSelectEntityDescription,
        coordinator: AquaTempCoordinator,
    ):
        super().__init__(coordinator)

        self._device_code = device_code
        self._api_data = self.coordinator.api_data[self._device_code]
        self._config_data = self.coordinator.config_data

        device_info = coordinator.get_device(device_code)
        device_name = device_info.get("name")

        entity_name = f"{device_name} {entity_description.name}"

        slugify_name = slugify(entity_name)

        device_id = self._api_data.get("device_id")
        unique_id = slugify(f"{entity_description.platform}_{slugify_name}_{device_id}")

        self.entity_description: AquaTempSelectEntityDescription = entity_description

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        temperature_unit = self.coordinator.get_temperature_unit(self._device_code)

        return temperature_unit

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.set_temperature_unit(self._device_code, option)

        await self.coordinator.async_request_refresh()
