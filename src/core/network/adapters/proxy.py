# -*- coding: utf-8 -*-

"""
    Proxy network transport placeholder.

    HTTP/SOCKS proxy handling remains inside existing request providers.
"""

from .base import BaseTransport


class ProxyTransport(BaseTransport):

    """Proxy transport adapter."""

    name = 'proxy'
