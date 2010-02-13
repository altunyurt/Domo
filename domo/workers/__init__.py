# ~*~ coding:utf-8 ~*~

from domo.plugins import registry
from domo.utils import find
from ctypes import Structure, c_uint32, c_char 
from sets import Set
from domo.interfaces.logger import get_logger
from multiprocessing.sharedctypes import Value


class Report(object):
    '''
        Shared memory object between service controller (pyro daemon) and crawler object.
        Stores and provides 3 informations:
            done : number of urls fetched
            todo : number of urls to be fetched 
            failed : number of urls that fetching failed for some reason 
    '''
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
    '''
        Shared memory object between service controller (pyro daemon) and crawler object.
        Stores and provides status information. 
    '''
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
        self.__status = Value(self.__STATUS, 'p')

    def set(self, st):
        setattr(self.__status, 'status', self._STATUS_.get(st))

    def get(self):
        for key, val in self._STATUS_.items():
            if val == self.__status.status:
                return key
        return None


""" TODO:
    Report and Status might have been combined in a single object, 
    i really do not remember why i chose this way. Upcoming versions 
    will have a much better schema.
"""

class Worker(object):

    def __init__(self, config, report=None, status=None):
        # TODO: format configuration items, everything is in list form for now
        self.name = config.get('options').get('name')[0]
        self.logger = get_logger(self.name)

        # shared objects 
        self.report = report
        self.status = status
        self.config = config

    def run(self):
        raise Exception('subclasses MUST implement this method')
   


