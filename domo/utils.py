# ~*~ coding:utf-8 ~*~
from copy import copy
from datetime import datetime
from random import choice
from socket import gethostname
from string import letters
from time import sleep, strftime, strptime
import statgrab as sg
import os
import re
import urllib

def find(lst, fn=lambda x: x):
    """Return the first matching element"""
    for el in lst:
        if fn(el):
            return el
    return None

def qsort(L):
    """quicksort"""
    if len(L) <= 1: return L
    return qsort( [ lt for lt in L[1:] if lt < L[0] ] )  +  \
                    [ L[0] ]  +  qsort( [ ge for ge in L[1:] if ge >= L[0] ] )

def generate_time_stamp():
    """
        generate YearMonthDayHourMinuteSecond
        formatted time stamp
    """
    now = datetime.now()
    return '%s.%s' % (now.strftime('%Y%m%d%H%M%S'), now.microsecond)

def getnodename():
    return gethostname().split('.')[0]

def node_info(pid):
    #pid = os.getpid()
    for proc in sg.sg_get_process_stats():
        if pid == proc.pid:
            break 
    load_stat = sg.sg_get_load_stats()
    mem_stats = sg.sg_get_mem_stats()
    swap_stats = sg.sg_get_swap_stats()

    return {
            'pid': pid,
            'loadavg' : {'min1':load_stat.min1},
            'cpu_usage': proc.cpu_percent,
            'mem_usage': proc.proc_resident,
        'node_mem_usage': mem_stats,
        'node_swap_usage': swap_stats,
    }

def generate_name(name):
    return '%s.%s.%s' % (name, getnodename(), generate_time_stamp())

def strtodict(arglist, seperator):
    d = dict()
    
    for arg in arglist:
        try:
            name, val = arg.split(seperator, 1)
        except ValueError:
            continue
        name = isinstance(name, str) and name.lower() or name
        d[name] = isinstance(val, list) and seperator.join(val) or val
    return d

def dicttostr(d):
    text = unicode('', 'utf-8')
    for key, val in d.items():
        text += u'%s: """%s"""\n' % (key, val)
    text += u'================================================='
    return text

def probeNS():
    # thread içinden çağırmamak lazım
    import Pyro.naming as naming
    from Pyro.errors import NamingError
    while True:
        try:
            ns = naming.NameServerLocator().getNS()
            break
        except NamingError:
            sleep(3)
    return ns

def create_random_id(length=20):
    return ''.join([choice(letters) for i in range(length)])

def normalize_price(val):
    # nedense milletçe fiyatları 1.096,59 şeklinde göstermeyi tercih etmişiz 
    if not val:
        return val

    f = re.compile('([0-9,.]+)')
    gr = f.search(val)
    if gr:
        t = gr.group()
        if t.find(',') != -1:
            return t.replace('.', '').replace(',', '.')
        return t
    return None

def currency(text, symbol):
    if text.lower().find(symbol.lower()) != -1:
        return normalize_price(text)
    return None

def first(l):
    if l:
        return l[0]
    return None

def check_if_contains(text, val):
    if val.lower() not in text.lower():
        return None
    return text

def urlquote(url):
    for x in copy(url):
        if ord(x) >= 127:
            url = url.replace(x, urllib.quote(x))
    return url

def normalize_date(timestamp):
    
    ts = strptime(timestamp, '%Y%m%d%H%M%S')
    return strftime('%m/%d/%Y %H:%M', ts)
