#~*~ coding:utf-8 ~*~

# database for management interface
MANAGEMENT_DATABASE = "mysql://tester:tester@localhost/domo"
MANAGEMENT_DATABASE_VERBOSE = False
MANAGEMENT_DATABASE_RECYCLE = 300

TEMPLATES_PATH = 'ui/templates/'
ARCHIVES_PATH = '/tmp/arcs/'
DOMAIN = "cbslab"

DEBUG = 10
INFO = 20
LOG_LEVEL = DEBUG
# want to see urls in the logs?
LOG_URLS = True
URL_MAX_TRIES = 5

CRAWL_OPTIONS = {
    "FOLLOWLOCATION": 0,
    "VERBOSE": 0,
    "MAXREDIRS": 0,
    "HEADER": True,
    "CONNECTTIMEOUT": 30,
    "POST": 0,
    "TIMEOUT": 300,
    "NOSIGNAL": 1,
    "SSL_VERIFYHOST": 0,
    "SSL_VERIFYPEER": 0,
    "USERAGENT": 'Mozilla/9.876 (X11; U; Linux 2.2.12-20 i686, en) Gecko/25250101)',
    "ENCODING": "gzip", # find some reasonable option here
    "COOKIEFILE": '/tmp/COOKIES', # make curl accept and use cookies
    "COOKIEJAR": '/tmp/COOKIES', # make curl accept and use cookies
}

