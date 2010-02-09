# ~*~ coding:utf-8 ~*~
from Pyro.core import ObjBase
from datetime import datetime
from domo.interfaces.logger import get_logger
from domo.utils import (node_info, getnodename, currency)
from domo.workers import Worker, Report, Status
from domo.workers.crawler import Crawler
from multiprocessing import Process
from multiprocessing.sharedctypes import Value
import os
import traceback
from copy import copy
import cjson

class WorkerService(ObjBase):

    def __init__(self):

        ObjBase.__init__(self)
        
        # {name : workerObj}
        self.workers = dict()
        self.logger = get_logger('WorkerService_%s' % getnodename())
        
    #def create(self, options, plugins):
    def create(self, config):
        """ parse config and create relevant classess """

        self.logger.debug('Creating new worker') 

        report = Report()                               # shared memory object: (done, todo)
        status = Status()                               # shared objects are
                                                        # used for simple
                                                        # information exchange

        config = cjson.decode(config)               # convert configuration to dictionary

        name = config.get('options').get('name')[0]             # will rewrite the name, ['name']
        version = datetime.today().strftime('%Y%m%d%H%M%S')
        name = '%s_%s_%s' % (name, version, getnodename())
        config.get('options')['name'] = [name]

        crawler = Crawler(config, report=report, status=status) # crawler instance created
                
        if crawler is not None:
            worker = Process(target=crawler.run, name=name)    # spawn a crawler process

            # shared memory: node ayağı
            worker.report = report
            worker.status = status

            # workeri listeye ekle
            self.workers.update({name: worker})
            self.logger.info('Created new worker: %s with status %s' % (name,
                                                                        worker.status.get()))
            # start the process, not the fetch job
            worker.start()
            
            return (True, '%s' % name)
        
        self.logger.error('Could not create new worker')
        return (False, 'Could not create new worker')


    def list(self):
        """list currently running workers"""
        self.logger.debug('Listing workers')
        return [(name, worker.status.get()) for name,worker  in self.workers.items()]
    
    def report(self, name):
        """get report data from the given worker"""

        if self.checkworker(name):
            worker = self.workers.get(name)
            self.logger.debug('Reporting worker: %s' % name)
            return (True, worker.report.get())

        self.logger.error('report: No such worker: %s' % name)
        return (False, 'No such worker: %s' % name)
    
    def pause(self, name):
        """stop worker"""

        if self.checkworker(name):
            self.workers.get(name).status.set('paused')
            
            self.logger.info('Worker paused: %s' % name)
            return (True, 'Worker %s paused' % name)

        self.logger.error('pause: No such worker: %s' % name)
        return (False, 'No such worker: %s' % name)
    
    def resume(self, name):
        """stop worker"""
        if self.checkworker(name):
            self.workers.get(name, None).status.set('running')
            
            self.logger.info('Resuming worker: %s' % name)
            return (True, 'Worker %s resumed' % name)

        self.logger.error('resume: No such worker %s' % name)
        return (False, 'No such worker: %s' % name)

    def kill(self, name):
        """terminate worker"""

        if self.checkworker(name):
            worker = self.workers.get(name)
            worker.status.set('killed')
            worker.join()

            self.logger.info('Worker terminated: %s' % name)
            return (True, 'Worker %s terminated' % name)
        
        self.logger.error('kill: No such worker: %s' % name)
        return (False, 'No such worker: %s' % name)

    def nodeinfo(self, name):
        """info about current process and node"""
        
        self.logger.debug('Node info requested')

        if self.checkworker(name):
            worker = self.workers.get(name)
            pid = worker.getPid()
            return (True, node_info(pid))
        
        return (False, 'No such worker %s' % name)

    def exit(self):
        self.logger.info('Node shutting down.. Terminating workers..')
        try:
            for name, worker in self.workers.items():
                # hack for enabling the daemoned mode
                if not self.checkworker(name):
                    continue
                worker.status.set('killed')
                worker.join()
                self.logger.info('Worker terminated: %s' % name)
        except:
            self.logger.error(traceback.format_exc())
            return (False, traceback.format_exc())
        return (True, 'Node %s shutdown', getnodename())

    def status(self, name):
        self.logger.debug('Status info requested')

        if not self.checkworker(name):
            return (False, 'No such worker %s' % name)

        return (True, '%s' % self.workers.get(name).status.get())
    
    def listjobs(self):
        self.logger.debug('Status info for all jobs requested')
        h = {}
        try:
            for name, worker in self.workers.items():
                # hack for enabling the daemoned mode
                if not self.checkworker(name):
                    continue
                h.update({name: {
                    'status':worker.status.get(), 
                    'report':worker.report.get()
                    }
                })
        except:
            self.logger.error(traceback.format_exc())
            return (False, traceback.format_exc())
        return (True, '%s' % cjson.encode(h))

    def checkworker(self, name=None):
        # worker varsa true donuyor
        if not name:
            #[worker.isAlive() for worker in self.workers.values()]
            [worker.is_alive() for worker in self.workers.values()]
            return 

        for wname, worker in self.workers.items():
            
            # status check 
            #st = worker.isAlive()
            st = worker.is_alive()

            if worker.status.get() in ('running','paused') and not st:
                worker.status.set('ended')

            if wname == name:
                return True
        return False
    
