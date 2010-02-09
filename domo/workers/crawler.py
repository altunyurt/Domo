# ~*~ coding:utf-8 ~*~

from cStringIO import StringIO
from datetime import datetime
from domo import settings
from domo.interfaces.darc import DArcWriter
from domo.interfaces.logger import get_logger
from domo.workers import Worker
from domo.workers.container import UrlsContainer
from sets import Set
import re
import os
import pycurl
import time
import traceback

t = re.compile('^[0-9]+$')

def create_multi(options):
    logger = get_logger('MULTIHANDLER')
    m = pycurl.CurlMulti()
    m.handles = []
    
    # default number of connections is 5
    # some options are hardcoded, nonprovided options 
    # might be problematic when settings.py is used 
    connection_count = int(options.get('maxconnections', [5])[0])
    logger.debug('maxconnections %d' % connection_count)

    for i in range(connection_count):
        c = pycurl.Curl()
        c.name = 'curl%s' % i

        # TODO: bu kısma, gerekli olan optionlar için uyarı koymak lazım

        if not hasattr(settings, 'CRAWL_OPTIONS'):
            logger.error('No options for crawler found')
            return None

        for opt, val in settings.CRAWL_OPTIONS.items():
            
            # use user provided options or defaults
            optval = options.get(opt.lower())  
            optval = optval and ( t.match(optval[0]) and int(optval[0]) or optval[0]) or val

            # optval is an external list
            c.setopt(getattr(pycurl, opt), val)
        m.handles.append(c)

    return m, m.handles[:]                  # multi, freelist


class Crawler(Worker):
    def __init__(self, *args, **kwargs):
        # initialize super's attributes
        super(self.__class__, self).__init__(*args, **kwargs)
        
        # create domo archive 
        self.darc = DArcWriter('%s' % os.path.join(settings.ARCHIVES_PATH, self.name))
        # initialize url container 
        self.container = UrlsContainer(self.config)
        self.options = self.config.get('options')

    def run(self):
        # renice the process with lowest priority
        os.nice(35)
        # start all
        return self.innerProcess()
    
    def innerProcess(self):

        self.logger.debug('Crawler started')
        # create curl handles
        multi, freelist = create_multi(self.options)
        
        maxconnections = len(freelist) 

        # main crawling loop 
        while True:
            
            st = self.status.get()
            if st == 'paused':
                time.sleep(1)
                continue

            elif st == 'ended':
                self.logger.debug('killed. exiting..')
                break

            # status 'running', so we are setting the urls here
            while freelist and self.container.queue:
           
                crawl_url = self.container.getnext()
                if crawl_url is None:
                    # we have no urls to crawl
                    break 

                # curl operations
                c = freelist.pop()
                c.body = StringIO()
                c.url = crawl_url

                c.setopt(pycurl.WRITEFUNCTION, c.body.write)

                c.setopt(pycurl.URL, crawl_url)
                multi.add_handle(c)
            
            while True:
          
                # perform fetching, i did never understand it here 
                ret, num_handles = multi.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break

            # Check for curl objects which have terminated, and add them to the freelist
            while True:
                num_q, ok_list, err_list = multi.info_read()

                # operating on successfuly fetched urls
                for c in ok_list:
                    # we may have been redirected to some other url 
                    current_url = c.getinfo(c.EFFECTIVE_URL)
                    self.logger.debug('Crawled url: %s' % current_url.decode('utf-8'))
                    
                    # remove handle from occupied list, to freelist 
                    multi.remove_handle(c)
                    freelist.append(c)

                    # add it whether or not we've fetched it
                    self.container.updatedone([c.url, current_url])
                    
                    content_type = c.getinfo(c.CONTENT_TYPE)
                    if not content_type :
                        # no content_type == no content
                        continue 

                    # processing text data
                    source = c.body.getvalue()
                    c.body.close()

                    # write archive file
                    self.darc.write(source, c, self)

                    if content_type.find('text') != -1:
                        pass
                   
                    self.container.process(source, c.url, current_url)
        

                for c, errno, errmsg in err_list:
                    url = c.getinfo(c.EFFECTIVE_URL)
                    
                    self.container.updatefailed([c.url, url])

                    multi.remove_handle(c)
                    freelist.append(c)
                
                if num_q == 0:
                    break


            # We just call select() to sleep until some more data is available.
            multi.select(1.0)
            self.report.set(
                done=len(self.container.done), todo=len(self.container.queue),
                failed=len(self.container.failed))
            
            if len(freelist) == maxconnections and len(self.container.queue) == 0:
                # ol sed'n dan
                break

        # Cleanup
        for c in freelist:
            if getattr(c, 'body', None):
                c.body.close()
                c.body = None
            c.close()
        multi.close()

        # close archive file
        self.darc.close()
        
        self.logger.info('Crawling ended')
        self.status.set('ended')



if __name__ == '__main__':
    from domo.workers import Status, Report

    configuration={'plugins':{
        'DomainFilter': ['http://example.com'],
        'HtmlExtractor': [], 
        'NoRepeatsFilter': [],
        'StripPatternTransform': [r'ssubmit=[0-9\.]+'],
    }, 

        'options' :{
            'name' : ['example'],
            'seeds':['http://example.com'],
            'connection_count':[10],
            'encoding': ['utf-8']}
    }

    c = Crawler(configuration, status=Status(), report=Report())
    try:
        c.run()
    except:
        c.darc.close()
        c.logger.error(c.container.done)

