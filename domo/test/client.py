# ~*~ coding:utf-8 ~*~
from Pyro.util import getPyroTraceback
from exceptions import Exception
from pprint import pprint
import Pyro.core
import Pyro.naming
import sys
import time 

plugins="""[
    ('SameDomainFilter', {'url':'http://www.someonlinestore.com'}),
    ('HtmlExtractor', {}),
    ('NoRepeatsFilter', {}),
    ('NotContainsFilter', {'terms': ('.css', '#', 'accounts', 'uye', 
        'etiket', 'jpg', 'gif', 'showCart', 'totalprice', 'suggest','teknikservis', 'wish',
        'review', 'form', 'uyelik',)}),
    ('AbsoluteTransform', {}),
    ('StripParentTransform', {}),
    ('StripSessionIdTransForm', {'expr':[r'ssubmit=[0-9\.]+']}),
    ('SortQParamsTransform', {}),
]""" 


options = """{
            'name' : 'some store',
            'start_url':'http://www.someonlinestore.com',
            'connection_count':2,
            'encoding': 'iso-8859-9',
            'parser_rules':
                [
                    {
                        'name': {'query':
                            '/html/body/div/div[4]/div[2]/div[2]/div[7]/div[2]/div/div/p[1]/text()',
                            'required': True,
                            'func': lambda x: isinstance(x, list) and x[0] or None,
                        },
                        'price_ytl': {'query': 
                            '/html/body/div/div[4]/div[2]/div[2]/div[7]/div[2]/div/div[3]/div[2]/p[2]/text()',
                            'required':False,
                            'func': lambda x: isinstance(x, list) and currency(x[0], "YTL") or None,
                        },
                        'price_dollar': {'query': 
                            '/html/body/div/div[4]/div[2]/div[2]/div[7]/div[2]/div/div[3]/div[2]/p[2]/text()',
                            'required':False,
                            'func': lambda x: isinstance(x, list) and currency(x[0], "$") or None,
                        },
                        'price_euro': {'query': 
                            '/html/body/div/div[4]/div[2]/div[2]/div[7]/div[2]/div/div[3]/div[2]/p[2]/text()',
                            'required':False,
                            'func': lambda x: isinstance(x, list) and currency(x[0], "EUR") or None,
                        },
                        'thumb_url': {'query': 
                            '/html/body/div/div[4]/div[2]/div[2]/div[7]/div/img/@src',
                            'required':True,
                            'func': lambda x: isinstance(x, list) and x[0] or None,
                        },
                        'category': {'query': 
                            '/html/body/div/div[4]/div[2]/div/div/ul//a/text()',
                            'required':True,
                            'func': lambda x: isinstance(x, list) and x[-1] or None,
                        },
                    }
                ]
    
            }""",
