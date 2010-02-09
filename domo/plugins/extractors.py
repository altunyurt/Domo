# ~*~ coding:utf-8 ~*~

from domo.plugins.__pluginmeta import Plugin, registry
from domo.utils import urlquote
from lxml import html, etree
from urlparse import urljoin
from domo.interfaces.logger import get_logger
from sets import Set
import re
import time
import traceback

LINK = {
      'a':              ('href',      ),
      'applet':         ('code',      ), 
      'area':           ('href',      ), 
      'bgsound':        ('src',       ), 
      'body':           ('background', ),
      'embed':          ('href',      ), 
      'embed':          ('src',       ), 
      'fig':            ('src',       ), 
      'frame':          ('src',       ), 
      'iframe':         ('src',       ), 
      'img':            ('href',      ), 
      'img':            ('lowsrc',    ), 
      'img':            ('src',       ), 
      'input':          ('src',       ), 
      'layer':          ('src',       ), 
      'object':         ('data',      ), 
      'overlay':        ('src',       ), 
      'script':         ('src',       ), 
      'table':          ('background', ),
      'td':             ('background', ),
      'th':             ('background', ),
      'rel':            (),
      'link':           ('href',),
};

class Extractor(Plugin):
    expr = re.compile('^(javascript:|mailto)', re.IGNORECASE)

class HtmlExtractor(Extractor):
    # yeniden yazmak gerek
    opts = {
        'enabled':True,
        'visible':False,
        'args_required':False,
    }
    
    def ignore(self, uri):
        if self.expr.match(uri):
            return None
        return uri

    def extract(self, source, url):

        try:
            tree = html.fromstring(source)
            tree.rewrite_links(self.ignore)
            tree.make_links_absolute(url, resolve_base_href=True)
        except:
            self.logger.error('Could not parse HTML %s' % traceback.format_exc())
            return Set([])
        
        uris = Set([])
        iterator = tree.getiterator()

        for link in iterator:
            #(<Element a at 40f7ee0c>, 'href', '../acupuncture8.shtml', 0)
            keywords = LINK.get(link.tag)
            if not keywords:
                continue

            # img, (src, lowsrc..) 
            for word in keywords:
                uri = link.get(word)
                if not uri:
                    continue
                try:
                    uris.add(urlquote(uri))
                except:
                    # link şema dandik
                    pass
        return uris

class XHtmlExtractor(Extractor):
    opts = {
        'enabled':False,
        'visible':False,
        'args_required':False,

    }

    def extract(self, source, url):

        try:
            tree = etree.fromstring(source, etree.XMLParser(recover=True,
                                                            ns_clean=True))
        except:
            self.logger.error('Could not parse HTML %s' % traceback.format_exc())
            return []
        
        links = set()
        iterator = tree.getiterator()

        for element in iterator:
            #(<Element a at 40f7ee0c>, 'href', '../acupuncture8.shtml', 0)
            #link = link[0]
            
            href = element.get('href')
            if not href or self.expr.match(href):
                continue

            href = urljoin(url, href)

            try:
                links.add(urlquote(href))
            except:
                # link şema dandik
                self.logger.error('XHtmlExtractor %s ' % traceback.format_exc())
                pass

        return list(links)

if __name__ in '__main__':
    from urllib2 import urlopen
    url = 'http://example.com'
    data  = urlopen(url).read()
    ext = XHtmlExtractor()
    print ext.extract(data, url)
