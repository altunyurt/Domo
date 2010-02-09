# ~*~ coding:utf-8 ~*~

from domo.plugins import registry
from domo import settings
from domo.interfaces.logger import get_logger
from sets import Set
import sys
import traceback


class UrlsContainer(object):
    def __init__(self, config):
        if not hasattr(self, 'logger'):
            self.logger = get_logger('UrlsContainer')
            
        self.options = config.get('options')
        self.plugins = config.get('plugins')
        self.done = Set([])
        # TODO: format configuration objects, everything is in list form
        self.queue = Set([item.strip().encode('utf-8') for item in self.options.get('seeds')[0].split(',')] or [])
        self.temp = Set([])
        self.failed = Set([])
        self.retries = dict()
        self.extractors = []
        self.filters = []
        self.transformers = []


        # TODO: rewrite
        # plugins = {plug: [params], plug2: [params2]}
        # plugins with no params where args_required will be discarded
        for name, parms in self.plugins.items():
            try:
                cls = registry.get(name)
                if cls.opts.get('args_required') and not parms[0]:
                    continue

                if name.endswith("Extractor"):
                    self.extractors.append(cls(parms))
           
                elif name.endswith("Filter"):
                    self.filters.append(cls(parms))
          
                elif name.endswith("Transform"):
                    self.transformers.append(cls(parms))
            except:
                self.logger.error('Loading of plugin %s failed\n\n %s' % (name,
                                                                         traceback.format_exc()))

        # also add enabled but non visible plugins to scene
        for name, cls in registry.items():
            try:
                if cls.enabled and not cls.visible:
                    if name.endswith("Extractor"):
                        self.extractors.append(cls())
        
                    elif name.endswith("Filter"):
                        self.filters.append(cls())
       
                    elif name.endswith("Transform"):
                        self.transformers.append(cls())
            except:
                self.logger.error('Loading of plugin %s failed\n\n %s' % (name,
                                                                         traceback.format_exc()))

      
    def process(self, source, initial_url, current_url):
        
        temp = Set([])
        for ext in self.extractors:
            temp.union_update(ext.extract(source, initial_url) or Set([]))

        for trs in self.transformers:
            temp = trs.transform(temp) or Set([])

        for flt in self.filters:
            temp = flt.filter(temp) or Set([]) 

        # now we have a set of urls
        # update queue with the ones that are not fetched before
        self.updatequeue(temp)


    def getnext(self):
        next = self.queue.pop()
        
        # until fetching completed, it'll be on temp
        self.temp.add(next)
        self.logger.debug(u'%s added to temp' % next.decode('utf-8'))
        return next

    def updatefailed(self, s):
        for url in s:
            
            retrcount = self.retries.get(url, 0)
            
            if retrcount >= self.options.get('MAX_RETRIES'):
                # update both done and failed
                self.failed.add(url)
                self.done.add(url)
                continue

            self.retries[url] = retrcount + 1
            self.queue.add(url)
    
    def updatequeue(self, s):
        '''s = Set([])'''
        if not isinstance(s, Set):
            s = Set(s)

        s.difference_update(self.done)
        s.difference_update(self.temp)
        
        self.queue.update(s)


    def updatedone(self, s):
        if not isinstance(s, Set):
            s = Set(s)
        
        # remove the urls from temporary storage
        self.temp.difference_update(s)
        self.done.update(s)
