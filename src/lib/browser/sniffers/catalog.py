# -*- coding: utf-8 -*-

"""Built-in sniffer registry metadata."""

from .descriptor import SnifferDescriptor


class SnifferCatalog:
    """Registry of known OpenDoor sniffers and their execution semantics."""

    DETECTOR = SnifferDescriptor.KIND_DETECTOR
    SUPPRESSOR = SnifferDescriptor.KIND_SUPPRESSOR
    ACTIVE = SnifferDescriptor.KIND_ACTIVE

    BUILTIN = (
        SnifferDescriptor('file', kind=DETECTOR, display_name='File', requires_body=False, priority=10),
        SnifferDescriptor('secret', kind=DETECTOR, display_name='Secret', requires_body=True, priority=20),
        SnifferDescriptor('indexof', kind=DETECTOR, display_name='IndexOf', requires_body=True, priority=30),
        SnifferDescriptor('stacktrace', kind=DETECTOR, display_name='StackTrace', requires_body=True, priority=40),
        SnifferDescriptor('malware', kind=DETECTOR, display_name='Malware', requires_body=True, priority=50),
        SnifferDescriptor(
            'skipempty',
            bucket='skip',
            kind=SUPPRESSOR,
            display_name='SkipEmpty',
            requires_body=True,
            priority=10,
        ),
        SnifferDescriptor(
            'skipsizes',
            bucket='skip',
            kind=SUPPRESSOR,
            display_name='SkipSizes',
            requires_body=False,
            priority=20,
        ),
        SnifferDescriptor(
            'collation',
            bucket='failed',
            kind=SUPPRESSOR,
            display_name='Collation',
            requires_body=True,
            priority=30,
        ),
        SnifferDescriptor('shadow', kind=ACTIVE, display_name='Shadow', requires_body=True, priority=10),
        SnifferDescriptor('openredirect', kind=ACTIVE, display_name='OpenRedirect', requires_body=False, priority=20),
    )

    def __init__(self, descriptors=None):
        """
        Create a sniffer catalog.

        :param list | tuple | None descriptors: descriptor values
        """

        self.__descriptors = list(descriptors or self.BUILTIN)
        self.__by_name = {descriptor.name: descriptor for descriptor in self.__descriptors}

    @classmethod
    def builtin(cls):
        """
        Create the built-in OpenDoor sniffer catalog.

        :return: SnifferCatalog
        """

        return cls()

    def names(self):
        """
        Return all known sniffer names in catalog order.

        :return: list[str]
        """

        return [descriptor.name for descriptor in self.__descriptors]

    def descriptor(self, name):
        """
        Return descriptor by public sniffer name.

        :param str name: public --sniff alias
        :return: SnifferDescriptor | None
        """

        return self.__by_name.get(str(name).lower())

    def enabled(self, names):
        """
        Return enabled descriptors in deterministic catalog order.

        :param list | tuple | set names: enabled public sniffer aliases
        :return: list[SnifferDescriptor]
        """

        enabled_names = {str(name).lower() for name in names or []}
        return [descriptor for descriptor in self.__descriptors if descriptor.name in enabled_names]

    def active(self, names):
        """
        Return enabled active sniffer descriptors.

        :param list | tuple | set names: enabled public sniffer aliases
        :return: list[SnifferDescriptor]
        """

        return [descriptor for descriptor in self.enabled(names) if descriptor.active]

    def suppressors(self, names):
        """
        Return enabled suppressor sniffer descriptors.

        :param list | tuple | set names: enabled public sniffer aliases
        :return: list[SnifferDescriptor]
        """

        return [descriptor for descriptor in self.enabled(names) if descriptor.suppressor]

    def detectors(self, names):
        """
        Return enabled passive detector descriptors.

        :param list | tuple | set names: enabled public sniffer aliases
        :return: list[SnifferDescriptor]
        """

        return [descriptor for descriptor in self.enabled(names) if not descriptor.active and not descriptor.suppressor]

    def requires_body(self, names):
        """
        Return True when any enabled sniffer requires response body.

        :param list | tuple | set names: enabled public sniffer aliases
        :return: bool
        """

        return any(descriptor.requires_body for descriptor in self.enabled(names))
