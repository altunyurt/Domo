# ~*~ coding:utf-8 ~*~

from domo.plugins.__pluginmeta import Plugin, registry
from domo.interfaces.logger import get_logger
from sets import Set
from urlparse import urlparse
import re

class Filter(Plugin):
    pass
    
class StartswithFilter(Filter):
    '''
        *OBSOLETE*
        Checks the given url's against the ..

    
    '''
    opts = {'enabled': False,
            'visible': False,
            'args_required': False,
    }

    def filter(self, urls):
        return filter(lambda x: x.startswith(self.args), urls)

class DomainFilter(Filter):
    '''
        Checks the given urls against the provided domain(s). Not specifying a domain filter will
        most probably result in an unlimited crawling session. Providing domain rules will limit the 
        urls that are to be fetched by crawler. Regex rules are applied.<br><br>

        <span class="exhead">Example:</span> providing 
        <span class='example'>.*.example.com </span> and <span class='example'>example2\.com</span> will match both
        <span class='example'>www.example.com</span> and
        <span class='example'>example2.com</span><br>

        >>> d = DomainFilter(['(ht|ft)tp://(\w+\.)?example.com','.*\.msn\.com'])
        >>> d.filter(['http://www.yahoo.com'])
        []
        >>> d.filter(['http://www.example.com','ftp://1example.com','https://live.msn.com'])
        ['http://www.example.com', 'https://live.msn.com']
    '''
    opts = {
        'enabled':True,
        'visible':True,
        'args_required': True,
    }

    def filter(self, urls):
        regx = re.compile("|".join(self.args), re.IGNORECASE)
        return filter(lambda x: regx.search(x), urls)


class ContainsFilter(Filter):
    '''
        Checks the given urls against the words in keywordslist.<br>
        picks the urls that contain at least one of these words.<br><br>

        Keywordslist consists of keywords seperated with commas<span
        class='example'>(,)</span><br><br>

        <span class="exhead">Example:</span> <span class='example'>some,
        keywords, else</span><br>

        >>> c = ContainsFilter(['some', 'url', 'here'])
        >>> c.filter(['http://somedomain.com', 'http://nokeyword.com', 'http://example.com/?keyw=here'])
        ['http://somedomain.com', 'http://example.com/?keyw=here']
    '''
    opts = {
        'enabled':True,
        'visible':True,
        'args_required':True,
    }

    def filter(self, urls):
        def p(url, terms):
            ''' search for the given term in given url '''

            for term in terms:
                if term in url:
                    return True
            return False

        return filter(lambda u: p(u, self.args), urls)

class NotContainsFilter(Filter):
    '''
        Checks the given urls against the words in keywordslist.<br> Drops the
        urls that contain at least one of these words<br><br>

        Keywordslist consists of keywords seperated with commas<span
        class='example'>(,)</span><br><br>

        <span class="exhead">Example:</span> <span class='example'>some,
        keywords, else</span><br>

        >>> c = NotContainsFilter(['some', 'url', 'here'])
        >>> c.filter(['http://somedomain.com', 'http://nokeyword.com', 'http://example.com/?keyw=here'])
        ['http://nokeyword.com']
    '''

    opts = {
        'enabled':True,
        'visible':True,
        'args_required':True,
    }

    def filter(self, urls ):
        def p(url, terms):
            for term in terms:
                if term in url:
                    return False
            return True
        
        return filter(lambda u: p(u, self.args), urls)

class NoRepeatsFilter(Filter):
    ''' 
        /foo/foo/foo/bar ve ?param=4&bisey=87&param=76
        gibi problemli urlleri çıkartıyoruz

        >>> c = NoRepeatsFilter([])
        >>> c.filter(['http://example.com/dir1/dir2/dir2/dir2/dir3',
        ... 'http://example.com/dir3/dir4/','http://example.com/?hede=1&hodo=2&hede=3' ])
        ['http://example.com/dir3/dir4/']

    '''
    opts = {
        'enabled':True,
        'visible':False,
        'args_required':False,
    }
    pathregx = re.compile(r'(/\w+)(?=\1)')
    paramregx = re.compile(r'[?&]+(\w+=)[^&*]&(?=.*\1)')

    def filter(self, urls):
        turls = filter(lambda x: not (self.pathregx.search(x) or
                                      self.paramregx.search(x)), urls)
        return turls

class ParentDepthFilter(Filter):
    '''
        Filters the urls exceeding the reverse depth according to provided
        seed(s):
            <span class="exhead">Example:</span> seed is http://example.com/dir1/dir2/dir3 and parentdepth is
            given as 2 which will allow urls like http://example.com/dir1/*
            if 0 is used as parentdepth http://example.com/dir1/dir2/dir3/* will
            be the base for all upcoming urls.


            >>> p = ParentDepthFilter([2])
            >>> p.filter(['http://example.com/path1','http://example.com/path1/path2/',
            ... 'http://example.com/path1/path2/path3','http://example.com/path1/path2/path3/../path4'])
            Set(['http://example.com/path1', 'http://example.com/path1/path2/'])


            bunun içeriği farklı olacak, parentdepth ters derinlikle ilgili.
            yani bulunduğun pathden ne kadar yukarı çıkabileceğini belirtiyor.
    '''
    opts = {
        'enabled':False,
        'visible': True,
        'default': -1,
        'args_required':True,
    }

    def filter(self, urls):
        if self.args <= -1:
            return urls
        depth = self.args[0]

        turls = Set([])
        for url in urls:
            path = [item for item in urlparse(url)[2].split('/') if item]
            if len(path) <= depth:
                turls.add(url)
        return turls


class RegexFilter(Filter):
    '''
        Checks the given urls against the supplied regular expression.<br>
        Arguments should be supplied in two tuples as <span class="example">
        (regex, 'drop/allow')</span>,<br> that 
        specifies whether the urls matching the reular expression will be kept
        or dropped.<br><br>

        <span class="exhead">Example:</span> <span class="example">('\w+\.com',
        'allow'), ('arg1=\w+', 'drop')</span> rule will drop urls like<br> 
        <span class='example'>http://example.com/?arg1=val&arg2=smt </span> and
        <span class='example'>http://example.net/fail</span> but will allow
        <span class='example'>https://example.com/blah1/blah2/</span>
        >>> r = RegexFilter([('\w+\.com', 'allow'), ('arg1=\w+', 'drop')])
        >>> r.filter(['https://example.com/blah1/blah2/','http://example.com/?arg1=val&arg2=smt', 'http://example.net/fail'])
        Set(['https://example.com/blah1/blah2/'])

    '''
    opts = {
        'enabled':True,
        'visible':True,
        'args_required':True,
    }


    def filter(self, urls):
        turls = urls

        def func(rgx, lst, allow=None):
            '''
               allow url if:
                   regex matches and is allowed
                   regex not matches and is not allowed
            '''
            urllist = list()
            for itm in lst:
                s = bool(rgx.search(itm))
           
                if not (s ^ allow):
                    urllist.append(itm)
            return urllist


        # self.args = [(regs, 'allow'), (regs, 'drop')]
        for regx, action in self.args:
            action = (action == 'allow')
            expr = re.compile(regx, re.IGNORECASE)
            turls = func(expr, turls, action)

        return Set(turls)


class DepthFilter(Filter):
    '''
        Picks the urls that has depth value less than or equal to given depth
        parameter.<br><br>

        <span class="exhead">Example:</span> 2 as depth value will pick <span
        class='example'>http://example.com/dir1/dir2</span> but not 
        <span class='example'>http://example.com/dir1/dir2/dir3</span>

        >>> d = DepthFilter([2])
        >>> d.filter(['http://example.com/path1','http://example.com/path1/path2/',
        ... 'http://example.com/path1/path2/path3','http://example.com/path1/path2/path3/../path4'])
        Set(['http://example.com/path1', 'http://example.com/path1/path2/'])
    '''
    opts = {
        'enabled':True,
        'visible':True,
        'args_required':True,
    }

    def filter(self, urls):
        maxdepth = self.args[0]
        temp = []

        if maxdepth in (None, -1):
            return urls
        
        for url in urls:
            if len(urlparse(url)[2].strip('/').split('/')) <= maxdepth:
                temp.append(url)

        return Set(temp)


        
if __name__ == '__main__':
    import doctest
    doctest.testmod()
