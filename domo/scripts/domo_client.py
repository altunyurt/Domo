#!/usr/bin/env python
# ~*~ coding:utf-8 ~*~

from Pyro.util import getPyroTraceback
from datetime import datetime
from domo import settings
from domo.interfaces.db import Profile, Job, Session, profile, job
from optparse import OptionParser
from pprint import pprint
from sqlalchemy.exceptions import InvalidRequestError
import Pyro.core
import Pyro.naming
import sys
import traceback
from domo.interfaces.logger import get_logger



domain = settings.DOMAIN

def listnodes(*args):
    logger = get_logger('Listnodes')

    ns = Pyro.naming.NameServerLocator().getNS()
    nlist = ns.list(':Default.%s' % domain)
    if not nlist:
        logger.error('No nodes found')
    else:
        logger.info('Nodes found: %s' % ", ".join([node[0] for node in nlist]))

    sys.exit(0)

def listprofiles(*args):
    logger = get_logger('ListProfiles')
    session = Session()
    profiles = session.query(Profile).all()

    if not profiles:
        logger.error('No profiles found')
    else:
        logger.info('Profiles found: %s' % ', '.join([profile.name for profile in profiles]))
    sys.exit(0)


def runcommand(options, parser):
    logger = get_logger('RunCommand')

    if not options.command or not options.node:
        return parser.print_help()

    #ns = Pyro.naming.NameServerLocator().getNS()
    #uri = ns.resolve('%s.%s.jobservice' % (domain, options.node))
    #js = Pyro.core.getProxyForURI(uri)
    js = Pyro.core.getProxyForURI("PYROLOC://localhost:7766/jobservice")

    if options.command == 'create':
        if not options.profile:
            return logger.error('crate should be called with profile name: -n nodename -c create -p profile')
            
        sess = Session()
        try:
            
            pf = sess.query(Profile).filter(profile.c.name==options.profile).first()
            status, workername = js.create(pf.configuration)

        except Exception, e:    
            logger.error( 'No profile found with name: %s' % options.profile)
            logger.error("".join(getPyroTraceback(e)))
            return -1

        if status: 
            j = Job(workername, 'paused')
            pf.jobs.append(j)
            #sess.save(j)
            sess.add(j)
            sess.commit()
            sess.close()
            logger.info ("worker with name %s created" % workername)
            return 0

        logger.error('no worker created: %s' % workername)
        return -1

    elif options.command == 'list':
        l = js.list()
        for worker, status in l:
            logger.info('%s: %s' % (worker, status))
    elif options.command == 'listjobs':
        s, l = js.listjobs()
        logger.info('%s' % l)
    else:
        if not options.worker:
            logger.error('%s should be called with a worker name: -n nodename -c %s -w workername' %  \
                (options.command, options.command))
            return -1

        try:
           status, retval = getattr(js, options.command)(options.worker)
        except Exception, e:
            logger.error("".join(getPyroTraceback(e)))
            
        
        d = {'kill':'killed', 'pause':'paused', 'resume':'running'}
        if options.command in d:
            s = Session()
            j = s.query(Job).filter(job.c.name==options.worker).one()
            j.status = d.get(options.command)

            if options.command == 'kill':
                j.end_date = datetime.now()
            s.commit()
            s.close()
        else:
            logger.info(retval)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--nlist', action='callback', callback=listnodes, help="List active nodes")
    parser.add_option('--plist', action='callback', callback=listprofiles, help="List profiles")
    parser.add_option('-c', '--command', 
                    choices=('create', 'pause', 'resume', 'report', 'status', 'list', 'kill', 'listjobs', 'nodeinfo'),
                    help="Crawler command. \n\
                        create: create a remote worker \n\
                        pause: pause a running worker. \n\
                        resume: resume a paused worker. \n\
                        report: get report from the specified worker. \n\
                        status: get status info of the specified worker. \n\
                        list: list workers on the node. \n\
                        kill: kill specified worker. \n\
                        listjobs: list all running instances and statuses \n\
                        nodeinfo: get node info. \n\
                        Commands are combined with following options""")
    parser.add_option('-n', '--node', help="Specifiy the node to be used")
    parser.add_option('-w', '--worker', help="Specifiy the worker to be used")
    parser.add_option('-p', '--profile', help="Specify site to be crawled")
   
    (options, args) = parser.parse_args(sys.argv) 
    
    runcommand(options, parser)
