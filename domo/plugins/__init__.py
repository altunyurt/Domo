# ~*~ coding:utf-8 ~*~

#class PluginMountMeta(type):
#    def __init__(cls, name, bases, attrs):
#        if not hasattr(cls, 'plugins'):
#            # This branch only executes when processing the mount point itself.
#            # So, since this is a new plugin type, not an implementation, this
#            # class shouldn't be registered as a plugin. Instead, it sets up a
#            # list where plugins can be registered later.
#            cls.plugins = []
#        else:
#            # This must be a plugin implementation, which should be registered.
#            # Simply appending it to the list is all that's needed to keep
#            # track of it later.
#            cls.plugins.append(cls)
#    
#
#class PluginMount(object):
#    def __init__(self, options={}, context={}):
#        self.options = options
#        self.context = context
#        # use the same logger object in any instance
#        self.logger = get_logger(self.__class__.__name__)
    

######################################################

from domo.plugins.__pluginmeta import Plugin
from domo.plugins.filters import Filter, registry
from domo.plugins.transformers import Transformer, registry
from domo.plugins.extractors import Extractor, registry
from copy import copy

for name, cls in copy(registry).items():
    # {name: class}

    if cls == Plugin or not getattr(cls, 'enabled', None):
            registry.pop(name)

