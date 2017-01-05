# -*- coding: utf-8 -*-


"""RegistryManager class"""

from .registry import Plugin
from plugins import *
from .exceptions import PluginError

class RegistryManager:
    """RegistryManager class"""

    def __int__(self):
        Plugin.register_plugin( logger )

    @staticmethod
    def load(name):
        try:
            plugin = Plugin()
            return plugin.plugins[name]
        except KeyError as p:
            raise PluginError('Cound not find plugin : {0}'.format(p))
