#!/usr/bin/env python
# ~*~ coding:utf-8 ~*~

#from Pyro.EventService import Clients
from Pyro.errors import PyroError,NamingError
#from domo.interfaces.daemonizer import Daemonizer
from Pyro.ext.daemonizer import Daemonizer
#from domo import settings
from domo.services import WorkerService
from domo.utils import find,probeNS
from domo.utils import getnodename
import Pyro
import Pyro.core
import Pyro.naming
import sys
import os
import signal


# TODO: non-threaded
def serverprocess():
    Pyro.config.PYRO_DETAILED_TRACEBACK = True
    Pyro.config.PYRO_TRACELEVEL = 0
    Pyro.config.PYRO_USER_TRACELEVEL = 4
    Pyro.config.PYRO_MULTITHREADED = 0                      # necessary for pyprocessing
    Pyro.core.initServer()

    # Get nameserver 
    #domain = settings.DOMAIN
    hostname = getnodename()
    #ns = probeNS()
    daemon = Pyro.core.Daemon()
    service = WorkerService()
    #daemon.useNameServer(ns)
    #publisher = Clients.Publisher()
                
    #buf = ''
    #for item in (domain, hostname):
    #    buf += ((buf != '') and '.' or '') + '%s' % item
    #    try:
    #        ns.createGroup('%s' % buf)
    #    except NamingError:
    #        pass

    #try:
    #    ns.unregister('%s.%s.jobservice' % (domain, hostname))
    #except NamingError:
    #    pass
    #daemon.connect(service, '%s.%s.jobservice' % (domain, hostname))
    daemon.connect(service, 'jobservice')
    
    # Tell everyone that there is a new guy in town
    #publisher.publish("JOBSERVICE", (hostname, 'started'))

    try:
        while 1:
            daemon.handleRequests(timeout=60, callback=service.checkworker())

    except KeyboardInterrupt:
        # tell service to shut down all workers
        service.exit()
        #publisher.publish("JOBSERVICE", (hostname, 'down'))
        #ns.deleteGroup('%s.%s' % (domain, hostname))


class ServerMain(Daemonizer):
    def __init__(self):
        Daemonizer.__init__(self)

    def main_loop(self):
        print 'Domo Server started'
        serverprocess()

if __name__ == '__main__':
    main = ServerMain()
    main.process_command_line(sys.argv)
