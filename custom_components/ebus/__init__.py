"""Integration between ebusd daemon for communication with eBUS heating systems, and Home Assistant using sensor component."""
"""ebusd: https://github.com/john30/ebusd"""
import logging
import threading
import ebusdpy
import voluptuous as vol

from homeassistant.const import (
    CONF_PORT,		#"port"
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ebus"
CONF_IPV4_ADDRESS = "ipv4_address"
DEFAULT_PORT = 8888
CONF_HUB_NAME = "hub_name" #if several ebusd demons are used they can be distinguish by a hub name
DEFAULT_HUB_NAME = "ebusd"
CONF_TIME_TO_LIVE = "time_to_live_s" #default time (in seconds) a ebusd value is valid before the ebusd demon reads a new value from the heating device

BASE_SCHEMA = vol.Schema({vol.Optional(CONF_HUB_NAME, default=DEFAULT_HUB_NAME): cv.string})

ETHERNET_SCHEMA = BASE_SCHEMA.extend(
    {
        vol.Required(CONF_IPV4_ADDRESS): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_TIME_TO_LIVE, default=30): cv.positive_int #read request: ebusd returns cached value if age is less 'time to live' in seconds. If no time value is specified at the sensor declaration the specified value here will be used for the sensor.
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [ETHERNET_SCHEMA])},
    extra=vol.ALLOW_EXTRA,
)

def setup(hass, config):
    """Set up eBUS component."""
    hass.data[DOMAIN] = hub_collect = {}

    for client_config in config[DOMAIN]:
        hub_name = client_config.get(CONF_HUB_NAME)
        hub_collect[hub_name] = EbusHub(client_config.get(CONF_IPV4_ADDRESS), client_config.get(CONF_PORT), client_config.get(CONF_TIME_TO_LIVE), hub_name)
        _LOGGER.debug("Setting up hub: %s", client_config)

    return True


class EbusHub:
    """Thread safe wrapper class for ebusdpy."""

    def __init__(self, ipaddress, port, time_to_live_s, name):
        """Initialize the eBUS hub."""
        self._name = name
        self._ipaddress = ipaddress
        self._port = port
        self._time_to_live_s = time_to_live_s
        self._lock = threading.Lock()

    @property
    def name(self):
        """Return the name of this hub."""
        return self._name

    def read(self, circuit, message_and_field, data_type, time_to_live_s):
        """Call the ebusdpy API to read a value from the eBUS device."""
        with self._lock:
            if time_to_live_s is None:
                time_to_live_s = self._time_to_live_s;
            _LOGGER.debug("ebus read (hub %s, IP %s:%i): read -m %d -c %s %s", self._name, self._ipaddress, self._port, time_to_live_s, circuit, message_and_field)
            return ebusdpy.read((self._ipaddress, self._port), circuit, message_and_field, data_type, time_to_live_s)

    def write(self, circuit, message, value):
        """Call the ebusdpy API to write a value to the eBUS device."""
        with self._lock:
            try:
                _LOGGER.debug("ebus write (hub %s, IP %s:%i): write -c %s %s %d", self._name, self._ipaddress, self._port, circuit, message, value)
                command_result = ebusdpy.write((self._ipaddress, self._port), circuit, message, value)
                if command_result is not None:
                    if "done" not in command_result:
                        _LOGGER.warning("ebus write error: write command failed")
            except RuntimeError as err:
                _LOGGER.error(err)

