# ~*~ coding:utf-8 ~*~

from domo.interfaces.logger import get_logger
from copy import copy
registry = {}                               # plugins container

class Plugin(object):
    '''
            'enabled': Boolean
                Plugin is enabled
            'visible': Boolean
                Plugin is visible in web interface - don't remember why i added this
            'args_required': Boolean
                Plugin requires arguments 
            'default': String
                Default value for plugin arguments, visible and modifiable via configuration
    '''
    class __metaclass__(type):
        def __init__(cls, name, bases, d):
            type.__init__(name, bases, d)
            if hasattr(cls, 'opts'):
                for key, val in cls.opts.items():
                    setattr(cls, key, val)
            registry.update({name: cls})

    def __init__(self, *args, **kwargs):
        self.logger = get_logger(self.__class__.__name__)
        

        if self.args_required:
            if not args:
                self.logger.info('%s requires arguments, but none given. therefore this module is disabled' % 
                        self.__class__.__name__)
                self.enabled = False
            else:
                self.args = copy(*args)                 # always in ['blah blah'] form
        else:
            self.args = []

        #self.logger.debug('%s: args %s' % (self.__class__.__name__, self.args))
