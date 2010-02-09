# ~*~ coding:utf-8 ~*~

from copy import copy
from domo import settings
from domo.interfaces.db import Session, Index
from domo.interfaces.logger import get_logger
from domo.utils import generate_time_stamp
import gzip
import os
import re

try:
    import psyco
    psyco.full()
except ImportError:
    pass

class DArcWriter(object):
    '''
        DArc(Domo Archive) Format:

        consists of 3 parts for each url.

        uridesc: 
           url time_stamp content_type data_length
        Header:
           header data received from the server
        Body:
           body data of the given url
    
    '''
    def __init__(self, filename):

        self.filename = filename.split('.')[0]              # trim extension
        self.file = gzip.GzipFile('%s_temp' % self.filename, 'wb')
        
        # if redirected, new url should be rewritten according to regex rules
        self.regx = re.compile(r'Location: (.*)\r\n')
        self.logger = get_logger('DArcWriter')

    def uridesc(self, curl):
        '''
            write uri description in the given format:
        '''
        # effective url == redirected (if) url
        #url = curl.getinfo(curl.EFFECTIVE_URL)
        url = curl.url

        # content_type of the data retrieved from given url
        content_type = curl.getinfo(curl.CONTENT_TYPE).split(';')[0]
        time_stamp = generate_time_stamp()

        return '%s %s %s' % (url, time_stamp, content_type)

    def write(self, source, curl, obj):
        '''
            write whole data to DArc file
        ''' 
        val = copy(source)

        content_length = len(val) + 1
        # needs format information
        self.file.write("%s %s\n%s\n" % (self.uridesc(curl), content_length, val))
        self.file.flush()

    def close(self):
        self.file.close() 
        os.rename('%s_temp' % self.filename, '%s.arc' % self.filename)
        self.logger.debug('Closed and moved file %s_temp to %s.arc' % (self.filename, self.filename))
        indexer('%s.arc' % self.filename)



class DArcReader(object):
    def __init__(self, filename):

        self.logger = get_logger('DArcReader')
        try:
            self.file = gzip.open(filename)
        except IOError:
            self.logger.error('File not found: %s' % filename)
            self.file = None

    def chunks(self):
        '''
            returns generator for archive data
            [uri, content_type, body_data]
        '''
        # http://example.com/ 20080131181302.72842 text/html 16548\n
        chunk_header = re.compile(r'^([^\s\t]+)\s([0-9\.]+)\s([^\s\t]+)\s([0-9]+)\n$')
        
        def strip_header(data):
            delim = re.compile(r'\r\n\r\n')
            header_check = re.compile('^[\s\t]*HTTP\/1\.[0-9]')
            
            temp = delim.split(data)

            for sect in temp:
                if not header_check.search(sect):
                    break
            return "".join(temp[temp.index(sect):])

        if self.file is None:
            self.logger.error('DArcReader should be first instantiated with a gzipped file')
        try:
            while 1:
                text = self.file.next()
                if not chunk_header.match(text):
                    continue
                uri, time_stamp, content_type, length = chunk_header.findall(text)[0]
                data = self.file.read(int(length))
                yield uri, content_type, strip_header(data)

        except StopIteration:
            self.file.close()
    
    def seek(self, offset):
        return self.file.seek(offset)

    def tell(self):
        return self.file.tell()

    def close(self):
        self.file.close()


'''
    indexer: filename
    reads and creates the index data for the given file
    TODO: better implementation needed
'''

def indexer(filename, max_count=100):
    logger = get_logger('Indexer')

    count = offset = 0
    sess = Session()
    d = DArcReader('%s' % filename)
    logger.debug('Archive file %s opened with pointer %s' % (filename, d))
    timestamp = filename.split('_')[1] # always profilename_timestamp_node.arc

    for chunk in d.chunks():
        # url : offset
        count += 1

        index = Index(filename, timestamp, chunk[0], offset)
        #sess.save(index)
        sess.add(index)
        if count % max_count == 0:
            sess.commit()
            sess = Session()

        offset = d.tell()
    sess.commit()
    d.close()
