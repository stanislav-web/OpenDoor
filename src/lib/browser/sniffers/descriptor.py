# -*- coding: utf-8 -*-

"""Shared sniffer descriptor primitives."""


class SnifferDescriptor:
    """Static metadata for one OpenDoor sniffer."""

    __slots__ = (
        'active',
        'bucket',
        'display_name',
        'kind',
        'name',
        'priority',
        'requires_body',
        'suppressor',
    )

    KIND_DETECTOR = 'detector'
    KIND_SUPPRESSOR = 'suppressor'
    KIND_ACTIVE = 'active'

    def __init__(self, name, bucket=None, kind=KIND_DETECTOR, display_name=None,
                 requires_body=False, priority=100):
        """
        Create a sniffer descriptor.

        :param str name: public --sniff alias
        :param str | None bucket: report bucket name
        :param str kind: detector, suppressor, or active
        :param str | None display_name: runtime display label
        :param bool requires_body: whether the sniffer requires response body
        :param int priority: deterministic execution priority within kind
        """

        self.name = str(name).lower()
        self.bucket = str(bucket or name).lower()
        self.kind = str(kind or self.KIND_DETECTOR).lower()
        self.display_name = display_name or self.name
        self.requires_body = True is requires_body
        self.priority = int(priority)
        self.active = self.kind == self.KIND_ACTIVE
        self.suppressor = self.kind == self.KIND_SUPPRESSOR

    def as_dict(self):
        """
        Return a serializable descriptor snapshot.

        :return: dict
        """

        return {
            'name': self.name,
            'bucket': self.bucket,
            'kind': self.kind,
            'display_name': self.display_name,
            'requires_body': self.requires_body,
            'priority': self.priority,
        }
