# -*- coding: utf-8 -*-

"""Active shadow-copy probe sniffer marker."""

from .provider import ResponsePluginProvider


class ShadowResponsePlugin(ResponsePluginProvider):
    """Register the active shadow-copy sniffer alias."""

    DESCRIPTION = 'Shadow Copy (probe backups for 200 OK file hits)'
    RESPONSE_INDEX = 'shadow'

    def __init__(self, void):
        """
        ResponsePluginProvider constructor.

        :param mixed void: optional plugin value, unused
        """

        ResponsePluginProvider.__init__(self)

    @classmethod
    def process(cls, response):
        """
        Keep shadow detection active-only.

        The Browser runtime owns shadow probes because they require additional
        requests. The response plugin exists only so --sniff shadow is resolved
        through the normal sniffer loader.

        :param response: HTTP response-like object
        :return: None because passive classification is intentionally disabled
        :rtype: None
        """

        return None
