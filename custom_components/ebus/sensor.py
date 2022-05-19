"""Support for eBUS sensors."""
import logging
import struct
from typing import Any, Optional, Union

import voluptuous as vol

from homeassistant.components.sensor import DEVICE_CLASSES_SCHEMA, PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_SENSORS,
    CONF_NAME,
    CONF_ICON,
    CONF_UNIT_OF_MEASUREMENT,
    ATTR_ENTITY_ID, #"entity_id"
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.restore_state import RestoreEntity

from . import CONF_HUB_NAME, DEFAULT_HUB_NAME, CONF_TIME_TO_LIVE, DOMAIN as EBUS_DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_CIRCUIT = "circuit"
CONF_MESSAGE = "message"
CONF_FIELD = "field_to_read"
CONF_DATA_TYPE = "data_type"
SERVICE_EBUS_WRITE = "ebus_write"
CONF_VALUE = "value"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend( #sensor definition
    {
        vol.Required(CONF_SENSORS): [
            {
                vol.Required(CONF_NAME): cv.string, #name of the sensor
                vol.Optional(CONF_ICON): cv.icon,
                vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
                vol.Optional(CONF_HUB_NAME, default=DEFAULT_HUB_NAME): cv.string, #specifies the ebus daemon name to use for this sensor (in case that there are sever ebus daemons)
                vol.Required(CONF_CIRCUIT): cv.string, #ebus circuit, see ebus csv file
                vol.Required(CONF_MESSAGE): cv.string,#ebus message, see 'name' in ebus csv file
                vol.Optional(CONF_FIELD, default=""): cv.string, #specifies the field name to read, see ebus csv file
                vol.Optional(CONF_DATA_TYPE, default=0): cv.positive_int, #0='float value', 1='time-schedule', 2='switch ON/OFF', 3='string', 4='value;status'
                vol.Optional(CONF_TIME_TO_LIVE, default=None): vol.Any(None, cv.positive_int) #read request: ebusd returns cached value if age is less 'time to live' in seconds
            }
        ]
    }
)

SERVICE_WRITE_SCHEMA = vol.Schema( #write service definition
    {
        vol.Optional(CONF_HUB_NAME, default=DEFAULT_HUB_NAME): cv.string, #hub name that should be used for the service call
        vol.Required(ATTR_ENTITY_ID): cv.entity_id, #sensor name e.g. 'sensor.xxxx' 
        vol.Required(CONF_VALUE): vol.Coerce(float),
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the eBUS sensors."""
    sensors = []

    for sensor in config.get(CONF_SENSORS):
        hub_name = sensor.get(CONF_HUB_NAME)
        hub = hass.data[EBUS_DOMAIN][hub_name]
        new_sensor = EbusSensor(
                        hub,
                        sensor.get(CONF_NAME),
                        sensor.get(CONF_ICON),
                        sensor.get(CONF_UNIT_OF_MEASUREMENT),
                        sensor.get(CONF_CIRCUIT),
                        sensor.get(CONF_MESSAGE),
                        sensor.get(CONF_FIELD),
                        sensor.get(CONF_DATA_TYPE),
                        sensor.get(CONF_TIME_TO_LIVE)
                    )
        sensors.append(new_sensor)

    if not sensors:
        return False

    add_entities(sensors, update_before_add=True)

    def ebus_write(service):
        """Write value eBUS device."""
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            target_sensors = [
                sensor for sensor in sensors if sensor.entity_id in entity_ids
            ]

            value = service.data.get(CONF_VALUE)
            for sensor in target_sensors:
                sensor.ebus_write(value)

    # Register services for ebus
    hass.services.register(EBUS_DOMAIN, SERVICE_EBUS_WRITE, ebus_write, schema=SERVICE_WRITE_SCHEMA)

class EbusSensor(RestoreEntity):
    """eBUS sensor."""

    def __init__(
        self,
        hub,
        name,
        icon,
        unit_of_measurement,
        circuit,
        message,
        field,
        data_type,
        time_to_live_s
    ):
        """Initialize the eBUS sensor."""
        self._hub = hub
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unit_of_measurement = unit_of_measurement
        self._circuit = circuit
        self._message = message
        self._field = field
        self._data_type = data_type
        self._time_to_live_s = time_to_live_s

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        state = await self.async_get_last_state()
        if not state:
            return
        self._attr_state = state.state

    def update(self):
        """Update the state of the sensor."""
        try:
            result = self._hub.read(self._circuit, (self._message + ' ' + self._field), self._data_type, self._time_to_live_s)
            if (result is None) or ("ERR:" in result):
                _LOGGER.error("Error reading ebusd from hub '%s', sensor '%s'", self._hub._attr_name, self._attr_name)
            else:
                self._attr_state = result
        except RuntimeError as err:
            _LOGGER.error(err)
            raise RuntimeError(err)

    def ebus_write(self, value):
        """Write a new value to the eBUS device (e.g. heatpump)."""
        try:
            self._hub.write(self._circuit, self._message, value)
        except RuntimeError as err:
            _LOGGER.error(err)
            raise RuntimeError(err)
