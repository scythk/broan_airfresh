"""Broan Air Fresh integration."""
from __future__ import annotations

import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import threading

DOMAIN = 'broan_airfresh'
CONF_HOST = "host"
CONF_PORT = "port"
CONF_ADDRESS = "address"

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT): cv.positive_int,
                vol.Optional(CONF_ADDRESS, default="00"): cv.string,
            }),
    },
    extra=vol.ALLOW_EXTRA)

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Your controller/hub specific code."""
    # Data that you want to share with your platforms
    conf = config[DOMAIN]
    hass.data[DOMAIN] = {
        'temperature': 23,
		"host": conf.get(CONF_HOST),
		"port": conf.get(CONF_PORT),
		"address": conf.get(CONF_ADDRESS)
    }

    # hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)
    hass.helpers.discovery.load_platform('fan', DOMAIN, {}, config)

    return True
