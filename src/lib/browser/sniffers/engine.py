# -*- coding: utf-8 -*-

"""Non-terminal sniffer engine primitives."""

from typing import ClassVar

from .catalog import SnifferCatalog
from .result import SnifferDecision


class SnifferEngine:
    """Run enabled sniffers without first-match conflicts."""

    KIND_DETECTOR = 'detector'
    KIND_SUPPRESSOR = 'suppressor'
    KIND_ACTIVE = 'active'

    KIND_ORDER: ClassVar[dict[str, int]] = {
        KIND_DETECTOR: 10,
        KIND_SUPPRESSOR: 20,
        KIND_ACTIVE: 30,
    }

    def __init__(self, enabled=None, sniffers=None):
        """
        Create a sniffer engine.

        :param list | tuple | set | None enabled: enabled sniffer names
        :param list | tuple | None sniffers: registered sniffer instances
        """

        self.enabled = {str(name).lower() for name in enabled or []}
        self.sniffers = list(sniffers or [])

    @classmethod
    def from_config(cls, config, sniffers=None):
        """
        Create a sniffer engine from browser config.

        :param object config: browser config with sniffers attribute
        :param list | tuple | None sniffers: registered sniffer instances
        :return: SnifferEngine
        """

        return cls(enabled=getattr(config, 'sniffers', None) or [], sniffers=sniffers)

    @classmethod
    def descriptors_from_config(cls, config, catalog=None):
        """
        Return enabled built-in descriptors from browser config.

        This is a registry helper for the migration period. Runtime still uses
        existing browser flows, while the engine owns stable sniffer metadata
        for future multi-finding orchestration.

        :param object config: browser config with sniffers attribute
        :param SnifferCatalog | None catalog: optional descriptor catalog
        :return: list[SnifferDescriptor]
        """

        registry = catalog or SnifferCatalog.builtin()
        return registry.enabled(getattr(config, 'sniffers', None) or [])

    @classmethod
    def active_descriptors_from_config(cls, config, catalog=None):
        """
        Return enabled active sniffer descriptors from browser config.

        :param object config: browser config with sniffers attribute
        :param SnifferCatalog | None catalog: optional descriptor catalog
        :return: list[SnifferDescriptor]
        """

        registry = catalog or SnifferCatalog.builtin()
        return registry.active(getattr(config, 'sniffers', None) or [])

    @classmethod
    def active_names_from_config(cls, config, catalog=None):
        """
        Return enabled active sniffer names from browser config.

        :param object config: browser config with sniffers attribute
        :param SnifferCatalog | None catalog: optional descriptor catalog
        :return: set[str]
        """

        return {descriptor.name for descriptor in cls.active_descriptors_from_config(config, catalog=catalog)}

    def registered_names(self):
        """
        Return registered sniffer names.

        :return: list[str]
        """

        return [self.__name(sniffer) for sniffer in self.sniffers]

    def active_names(self):
        """
        Return enabled registered sniffer names in engine execution order.

        :return: list[str]
        """

        return [self.__name(sniffer) for sniffer in self.__selected_sniffers()]

    def run_passive(self, context):
        """
        Run enabled passive sniffers and suppressors.

        :param SnifferContext context: response context
        :return: SnifferDecision
        """

        decision = SnifferDecision()

        for sniffer in self.__selected_sniffers():
            if self.__kind(sniffer) == self.KIND_ACTIVE:
                continue

            decision.extend(self.__match(sniffer, context))

        return decision

    def run_active(self, context):
        """
        Run enabled active sniffers.

        :param SnifferContext context: response context
        :return: list[SnifferResult]
        """

        findings = []

        for sniffer in self.__selected_sniffers():
            if self.__kind(sniffer) != self.KIND_ACTIVE:
                continue

            findings.extend(self.__match(sniffer, context))

        return findings

    def __selected_sniffers(self):
        """
        Return enabled sniffers in deterministic engine order.

        :return: list
        """

        selected = [sniffer for sniffer in self.sniffers if self.__name(sniffer) in self.enabled]
        return sorted(selected, key=self.__sort_key)

    def __sort_key(self, sniffer):
        """
        Build deterministic execution order for one sniffer.

        :param object sniffer: sniffer instance
        :return: tuple
        """

        return (
            self.KIND_ORDER.get(self.__kind(sniffer), 100),
            int(getattr(sniffer, 'PRIORITY', 100)),
            self.__name(sniffer),
        )

    @staticmethod
    def __name(sniffer):
        """
        Return normalized sniffer name.

        :param object sniffer: sniffer instance
        :return: str
        """

        return str(getattr(sniffer, 'NAME', '')).lower()

    @classmethod
    def __kind(cls, sniffer):
        """
        Return normalized sniffer kind.

        :param object sniffer: sniffer instance
        :return: str
        """

        kind = str(getattr(sniffer, 'KIND', cls.KIND_DETECTOR)).lower()
        if kind not in cls.KIND_ORDER:
            return cls.KIND_DETECTOR
        return kind

    @staticmethod
    def __match(sniffer, context):
        """
        Run one sniffer and normalize empty results.

        :param object sniffer: sniffer instance
        :param SnifferContext context: response context
        :return: list[SnifferResult]
        """

        results = sniffer.match(context)
        if results is None:
            return []
        if isinstance(results, (list, tuple)):
            return list(results)
        return [results]
