#! ~*~ coding:utf-8 ~*~

from datetime import datetime
from domo import settings
import logging
import sys
import traceback


"""
    TODO: logging should be much more clear
"""



class ConsoleHandler(logging.StreamHandler):
    """log to console for debugging"""
    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.setFormatter(
                logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))


class FileHandler(logging.FileHandler):
    """log to file for debugging"""
    def __init__(self, filename):
        logging.FileHandler.__init__(self, filename)
        self.setFormatter(
                logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))

def get_logger(name, handler=ConsoleHandler):
    """return logger instance"""
    logger = logging.getLogger(name)
    
    if not logger.handlers and  \
        not [isinstance(h, handler) for h in logger.handlers]:
        logger.addHandler(handler())

    logger.setLevel(settings.LOG_LEVEL)
    return logger
