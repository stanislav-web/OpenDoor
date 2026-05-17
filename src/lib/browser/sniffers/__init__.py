# -*- coding: utf-8 -*-

"""Sniffer engine primitives."""

from .catalog import SnifferCatalog
from .context import SnifferContext
from .descriptor import SnifferDescriptor
from .engine import SnifferEngine
from .result import SnifferDecision, SnifferResult

__all__ = [
    'SnifferCatalog',
    'SnifferContext',
    'SnifferDecision',
    'SnifferDescriptor',
    'SnifferEngine',
    'SnifferResult',
]
