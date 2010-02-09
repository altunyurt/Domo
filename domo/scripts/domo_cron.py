#!/usr/bin/env python
# ~*~ coding:utf-8 ~*~

from Pyro.util import getPyroTraceback
from datetime import datetime
from domo import settings
from domo.interfaces.db import Site, Job, makelogsession
from optparse import OptionParser
from sqlalchemy.exceptions import InvalidRequestError
from domo.interfaces.logger import get_logger
from datetime import datetime, timedelta
import Pyro.core
import Pyro.naming
import sys
import traceback

domain = settings.DOMAIN
logger = get_logger('Cron service')

def listnodes(ns):
    nlist = ns.list(':Default.%s' % domain)

    if not nlist:
        logger.error('No nodes found, exiting')
        return None
    return [node[0] for node in nlist]

def listsites():
    session = makelogsession()()
    sites = session.query(Site).all()
    
    if not sites:
        logger.error('No sites found, exiting')
        return None
    return sites

# util func, compare two tuples
def cmp(a,b):
    if a[1] > b[1]:
        return 1
    elif a[1] < b[1]:
        return -1
    return 0

def create(ns, site, nodes):

    jslist = []
    if not (site.not_before and site.not_after):
        logger.warn('not_after or not_before not set, passing %s' % site.name)
        return None

    for node in nodes:
        uri = ns.resolve('%s.%s.jobservice' % (domain, node))
        js = Pyro.core.getProxyForURI(uri)

        jslist.append((js, js.list()))

    # en az ise gore siralyoruz
    jslist.sort(cmp=cmp)
    
    js = jslist[0][0]
    options1,options2 = site.options.split('{', 1)
    options = options1 + "{'not_after':'%s','not_before':'%s'," % \
                                    (site.not_after, site.not_before) + options2

    try:
        print options
        status, name = js.create(options, site.plugins)
        if not status:
            logger.error('Could not create worker for %s error was "%s"' % (site.name, name))
            return None
    except Exception, e:
        logger.error('Could not create worker for  %s error was "%s"' %
                     (site.name, pprint(getPyroTraceback(e))))
        return None
    
    try:
        status, mesg = js.start(name)
    except Exception, e:
        logger.error('Could not start worker  %s error was "%s"' % (name, getPyroTraceback(e)))
        return None
     

    try:
        sess = makelogsession()()
        job = Job(name=name, status='running')
        job.not_before = site.not_before
        job.not_after = site.not_after

        job.site = site.id
        #sess.save(job)
        sess.add(job)
        sess.commit()
        logger.info('Created job %s for site %s' % (name, site.name))
        return True
    except:
        logger.error('Could not save job information for %s error was %s' % (site.name,
                                                                   traceback.format_exc()))
        return None
    
def getlastjob(site):
    ses = makelogsession()()
    job = ses.query(Job).filter(Job.site==site.id).order_by('-end_date').first()
    if not job:
        return None
    return job.end_date




if __name__ == '__main__':

    ns = Pyro.naming.NameServerLocator().getNS()
    nodes = listnodes(ns)
    sites = listsites()
    now = datetime.now()

    if not (nodes and sites):
        sys.exit(-1)
    
    for site in sites:
        last_job_end_date = getlastjob(site)
        hours = int(site.fetch_interval)
        if last_job_end_date is None or now - last_job_end_date >= timedelta(hours=hours):
            create(ns, site, nodes)
        
