# ~*~ coding:utf-8 ~*~

from domo.plugins.__pluginmeta import Plugin, registry
from domo.utils import qsort
from sets import Set
import posixpath
import re
import urllib2
import urlparse


class Transformer(Plugin):
    pass

class StripPatternTransform(Transformer):
    '''
        Rewrites the urls by  stripping off the patterns that matches the
        supplied regular expression.<br><br>

        <span class="exhead">Example:</span> <span class='example'>jsessionid=[\w]*&?</span> 
        pattern will transform the url in form<br>
        <span
        class='example'>http://example.com/blah?jsessionid=123675743572aedf2342&param=value</span><br> to
        <span class='example'>http://example.com/blah?param=value</span>

        >>> s = StripPatternTransform([
        ...    'jsessionid=[\w]*&?|sid=[\w]*&?|\(s\([0-9a-z]+\)\)',
        ...    '\(\(\w+\)\)/?', 'id=\w+&?'])
        >>> s.transform(['http://example.com/((S23468362t362356tf234))/deneme',
        ...    'http://example.com/?some=one&id=456gh&another=one'])
        Set(['http://example.com/?some=one&another=one', 'http://example.com/deneme'])
    '''
    opts = {
        'enabled':True,
        'visible':True,
        'default':'jsessionid=[\w]*&?|sid=[\w]*&?|\(s\([0-9a-z]+\)\)',
        'args_required': True,
    }

    def transform(self, urls):
        regx = re.compile('|'.join(self.args), re.IGNORECASE)
        temp = Set([])
        for url in urls:
            url = regx.sub('', url)
            url and temp.add(url)
        return temp

    
class SortParamsTransform(Transformer):
    ''' 
        sort the query parameters. this way we make sure that we are not 
        requesting the same page again 
        
        >>> s = SortParamsTransform([])
        >>> s.transform(['http://example.com/?one=1&two=2&three=3',
        ...     'http://example.com/?vge=34ads&w323de=23434&ade=234'])
        Set(['http://example.com/?one=1&three=3&two=2', 'http://example.com/?ade=234&vge=34ads&w323de=23434'])
    '''
    # TODO: bunu biraz temizlemek gerek 
    opts = {
            'enabled':True,
            'visible': False,
            'args_required': False,
    }
    
    expr = re.compile(r'(\?[^?]*)$', re.IGNORECASE)
    splitter = re.compile(r'&(?:amp;)?')

    def transform(self, urls):
        temp = Set([])
        def sortparams(url, regx):
            match = regx.search(url)
            if match:
                uri = regx.split(url)[0]
                qstr = match.group()
                # no repeating qstr
                qlist = list(set(self.splitter.split(qstr[1:])))
                return '%s?%s' % (uri, '&'.join(qsort(qlist)))
            return url
        for u in urls:
            temp.add(sortparams(u, self.expr))
        #return map(lambda url: sortparams(url, self.expr), urls)
        return temp

class NormalizeUrlTransform(Transformer):
    ''' 
        
        strip fragments(#somefragment) from the urls, rewrite urls according to
        parent paths 
    
        >>> s = NormalizeUrlTransform([])
        >>> s.transform(['http://example.com/deneme#somefragment',
        ... 'http://example.com:8000/deneme/?param=value&param2=value2#frags',
        ... 'https://example.com/../deneme/../..///../path/deneme/',
        ... 'http://example.com'])
        Set(['https://example.com/path/deneme/', 'http://example.com', 'http://example.com:8000/deneme/?param=value&param2=value2', 'http://example.com/deneme'])
    
    '''
    opts = {
        'enabled':True,
        'visible':False,
        'args_required': False,
    }

    def normalize(self, url):
        turl = urlparse.urlparse(url)
        slashed = turl[2].endswith('/')
        
        # path information ('/some/../path that needs to be taken care_of /..///..')
        path = turl[2] and posixpath.normpath(turl[2].replace(' ','%20')) or ''
        #path = turl[2] and posixpath.normpath(urllib2.quote(turl[2])) or ''

        return urlparse.urlunparse(
            (turl.scheme,turl.netloc, '%s%s' % (path, slashed and '/' or ''), turl.params, turl.query, ''))
            

    def transform(self, urls):
        temp = Set([])

        for url in urls:
            url = self.normalize(url)
            url and temp.add(url)
        
        return temp



if __name__ == '__main__':
    import doctest 
    doctest.testmod()


