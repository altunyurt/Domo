# ~*~ coding: utf-8 ~*~
'''
    Should be a completely separate module.

'''
from copy import copy
from domo.interfaces import db
from domo.interfaces.logger import get_logger
from domo.utils import dicttostr, currency
from domo.settings import LOG_LEVEL, DEBUG
from sqlalchemy import and_
from lxml import etree
from pprint import pprint
import codecs
import sys
import traceback
from datetime import datetime

class Parser(object):

    def __init__(self, config, logger):
        self.htmlparser = etree.HTMLParser(recover=True)
        self.xmlparser = etree.XMLParser(recover=True, ns_clean=True)

        self.config = config.get('parser_rules')
        self.site_name = config.get('name')
        self.encoding = config.get('encoding') or 'utf-8'
        self.logger = logger
        self.stores = {}
        sess = db.makesession()()
        for store in sess.query(db.Store).all():
            self.stores.update({store.store_name.lower(): store.id})
        sess.close()

    
    def parse(self, source, url, extfunc=None):
        if not self.config:
            return 

        def apply_rule(tree, ops):
             try:
                els = tree.xpath(ops['query'])
             except:
                self.logger.debug('Xpath operation failed: %s %s %s' %
                                  (ops['query'], traceback.format_exc(), url))
                return None

             try:
                if els:
                    result = 'func' in ops and ops['func'](els) or els
                    return result
                    #if isinstance(result, basestring):
                    #    return result.strip()
             except:
                self.logger.error('Parser_apply_rule: %s' % traceback.format_exc())

             return None


        try:
            # convert to utf-8 encoded unicode string
            source = unicode(source, self.encoding.strip(), 'replace')
            
            doctype = 'html'
            #if source[:100].find('XHTML') != -1:
            #    doctype = 'html'
            
            if doctype == 'xhtml':
                tree = etree.fromstring(source, self.xmlparser)
            else:
                tree = etree.fromstring(source, self.htmlparser)

            # Sometimes tree is None. I don't know why this happens, but it happens.
            if tree is None:
                return None
            
            retval = {}

            for ruleset in copy(self.config):

                for rule_name, rule in copy(ruleset).items():
                    val = apply_rule(tree, rule)
                    # bir şekilde beklenen pathi tutmamışsa, yanlışlık var demektir,
                    # rule'u terket, sıradakini dene
                    if rule['required'] and not val:
                        retval = {}
                        break
                    
                    # val = None, required=False ise hala sorun yok 
                    if val:
                        retval.update({rule_name: val})
                if retval:
                    # url zaten unicode
                    retval.update({'url':url})
                    if LOG_LEVEL == DEBUG:
                        self.logger.debug("\nParsed data (will not be saved to db):\n")
                        if extfunc:
                            retval = extfunc(retval)
                        print "%s" % dicttostr(retval).encode('utf-8')
                    else:
                        self.save_data(retval)
        except:
            self.logger.error('Parser_main: %s' % traceback.format_exc())
        
        return 
    def save_data(self, data):
        # name, category_id, store_id, search_title, url, description=None, 
        # price_ytl = None, price_dollar=None, price_euro=None, vat_rate=None

        store_id = self.stores.get(self.site_name.lower())
        # var mı diye yoklamalı
        session = db.makesession()()
        try:
            former = session.query(db.StoreProductTemp).filter(
                        and_(db.StoreProductTemp.product_name==data.get('name').encode('utf-8'), 
                             db.StoreProductTemp.url==data.get('url').encode('utf-8'))).first()
            former.store_id = store_id
            former.thumb_url = data.get('thumb_url').encode('utf-8')
            former.price_ytl = data.get('price_ytl')
            former.price_dollar = data.get('price_dollar')
            former.price_euro = data.get('price_euro')
            former.vat_rate = 18 # TODO: hardcode
            former.last_update = datetime.now()
            former.description = data.get('description')
            session.commit()
            self.logger.debug('updated %s' % former.product_name) 

        except:
            try:
                sp = db.StoreProductTemp(data.get('name'),
                        1, # category_id için ne yapmalı
                        store_id,
                        'sorctaytil', 
                        data.get('url'),
                        description = data.get('description'),
                        thumb_url = data.get('thumb_url'),
                        price_ytl = data.get('price_ytl'), 
                        price_dollar = data.get('price_dollar'), 
                        price_euro = data.get('price_euro'),
                        vat_rate = 18)
                sp.save()

            except:
                self.logger.error('Parser_save_data: %s' % traceback.format_exc())
        session.close()
