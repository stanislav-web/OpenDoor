# -*- coding: utf-8 -*-

"""Active open redirect verification sniffer marker."""

from .provider import ResponsePluginProvider


class OpenredirectResponsePlugin(ResponsePluginProvider):
    """Register the active open redirect sniffer alias."""

    DESCRIPTION = 'Open Redirect (verify controlled external redirect targets)'
    RESPONSE_INDEX = 'openredirect'

    def __init__(self, void):
        """Create response plugin marker.

        :param mixed void: optional plugin value, unused
        """

        ResponsePluginProvider.__init__(self)

    @classmethod
    def process(cls, response):
        """Keep open redirect detection active-only.

        The Browser runtime owns active verification because it requires
        controlled follow-up requests. The plugin exists only so
        --sniff openredirect is resolved through the normal sniffer loader.

        :param response: HTTP response-like object
        :return: None because passive classification is intentionally disabled
        :rtype: None
        """

        return None
