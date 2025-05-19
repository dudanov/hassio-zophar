"""Expose Zophar Browser as a media source."""

from __future__ import annotations

from typing import override

from homeassistant.components.media_player.const import MediaClass
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
    Unresolvable,
)
from homeassistant.core import HomeAssistant, callback
from zophar import GameListPage, GamePage, InfoPage, ZopharBrowser

from . import ZopharConfigEntry
from .const import DOMAIN


async def async_get_media_source(hass: HomeAssistant) -> ZopharMediaSource:
    """Set up Zophar Browser media source."""

    # Zophar supports only a single config entry
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    return ZopharMediaSource(hass, entry)


class ZopharMediaSource(MediaSource):
    """Provide Zophar resources as media sources."""

    name = "Zophar Browser"
    urls: dict[str, str]

    def __init__(self, hass: HomeAssistant, entry: ZopharConfigEntry) -> None:
        """Initialize ZopharMediaSource."""

        super().__init__(DOMAIN)
        self.hass = hass
        self.entry = entry
        self.urls = {}

    @property
    def zophar(self) -> ZopharBrowser:
        """Return the Zophar API client."""

        return self.entry.runtime_data

    @override
    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve selected Zophar station to a streaming URL."""

        path, _, id = item.identifier.rpartition("/")

        game = await self.zophar.gamepage(path)

        if url := game.tracks[int(id)].mp3url:
            return PlayMedia(str(url), "audio/mpeg")

        raise Unresolvable("Unknown media.")

    @callback
    def _menu_folders(self) -> list[BrowseMediaSource]:
        return [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=f"_{title}",
                media_class=MediaClass.DIRECTORY,
                media_content_type="",
                title=title,
                can_play=False,
                can_expand=True,
            )
            for title in self.zophar.menu
        ]

    @callback
    def _menu_folder_items(self, id: str) -> list[BrowseMediaSource]:
        return [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=item.path,
                media_class=MediaClass.DIRECTORY,
                media_content_type="",
                title=item.name,
                can_play=False,
                can_expand=True,
            )
            for item in self.zophar.menu[id]
            if not item.path.startswith("/")
        ]

    @override
    async def async_browse_media(
        self, item: MediaSourceItem
    ) -> BrowseMediaSource:
        """Return media."""

        if id := item.identifier:
            if id.startswith("_"):
                # Menu category
                children = self._menu_folder_items(id[1:])

            else:
                # Real server paths

                page = await self.zophar.page(id)

                match page:
                    case GamePage(tracks=tracks):
                        children = [
                            BrowseMediaSource(
                                domain=DOMAIN,
                                identifier=f"{id}/{idx}",
                                media_class=MediaClass.TRACK,
                                media_content_type="audio/mpeg",
                                title=f"{track.title} ({track.length.seconds // 60}:{track.length.seconds % 60:02})",
                                can_play=True,
                                can_expand=False,
                            )
                            for idx, track in enumerate(tracks)
                        ]

                    case GameListPage():
                        children = [
                            BrowseMediaSource(
                                domain=DOMAIN,
                                identifier=game.path,
                                media_class=MediaClass.GAME,
                                media_content_type="",
                                title=game.name,
                                can_play=False,
                                can_expand=True,
                                thumbnail=game.cover
                                and str(game.cover),
                            )
                            for game in await self.zophar.gamelist(id)
                        ]

                    case InfoPage(entries=entities):
                        children = [
                            BrowseMediaSource(
                                domain=DOMAIN,
                                identifier=x.path,
                                media_class=MediaClass.DIRECTORY,
                                media_content_type="",
                                title=x.name,
                                can_play=False,
                                can_expand=True,
                            )
                            for x in entities
                        ]

        else:
            # Menu folders
            children = self._menu_folders()

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.APP,
            media_content_type="",
            title=self.entry.title,
            can_play=False,
            can_expand=True,
            children=children,
        )
