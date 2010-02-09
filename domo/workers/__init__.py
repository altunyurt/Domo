# ~*~ coding:utf-8 ~*~
from domo.plugins import registry
from domo.utils import find
from ctypes import Structure, c_uint32, c_char 
from sets import Set
from domo.interfaces.logger import get_logger
from processing.sharedctypes import Value


class Report(object):
    class __REPORT(Structure):
        _fields_ = (('done', c_uint32), ('todo', c_uint32), ('failed', c_uint32))

    def __init__(self):
        self.__report = Value(self.__REPORT, 0)


    def set(self, *args, **kwargs):
        for key, val in kwargs.items():
            setattr(self.__report, key, val)

    def get(self):
        return dict([(item, getattr(self.__report, item)) for item in ('done',
                                                                       'todo',
                                                                       'failed')])

class Status(object):
    _STATUS_ = {
        #'pending':'g',
        'paused': 'p',
        'running': 'r',
        #'killed': 'k',
        'ended': 'e',
    }
    class __STATUS(Structure):
        _fields_ = (('status', c_char),)

    def __init__(self):
        # doğrudan __Statuste hallediyorduk daha önce,
        # ama sonra processing structure'dan türeyen classların 
        # atributelarını almamaya başladı, o yüzden dandik bir wrapper yapmak
        # yoluna gittim
        self.__status = Value(self.__STATUS, 'p')

    def set(self, st):
        setattr(self.__status, 'status', self._STATUS_.get(st))

    def get(self):
        for key, val in self._STATUS_.items():
            if val == self.__status.status:
                return key
        return None

class Worker(object):

    def __init__(self, config, report=None, status=None):
        # TODO: format configuration items, everything is in list form for now
        self.name = config.get('options').get('name')[0]
        self.logger = get_logger(self.name)

        # shared objects 
        self.report = report
        self.status = status
        self.config = config


    # pluginler urlcontainer mevzuu için geçerli olmalı
    # container class nerede olmalı nasıl olmalı bilemiyorum tabii
        
    def run(self):
        raise Exception('subclasses MUST implement this method')
   


