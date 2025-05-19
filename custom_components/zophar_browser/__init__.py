"""The Zophar Browser integration."""

from __future__ import annotations

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from zophar import ParseError, ZopharBrowser

type ZopharConfigEntry = ConfigEntry[ZopharBrowser]


async def async_setup_entry(
    hass: HomeAssistant, entry: ZopharConfigEntry
) -> bool:
    """Set up Zophar Browser from a config entry.

    This integration doesn't set up any entities, as it provides a media source
    only.
    """

    session = async_get_clientsession(hass)
    zophar = ZopharBrowser(session=session)

    try:
        await zophar.open()

    except (ClientError, ParseError):
        raise ConfigEntryNotReady

    entry.runtime_data = zophar

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    return True
