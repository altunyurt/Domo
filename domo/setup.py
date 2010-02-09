from distutils.core import setup
import os

setup(
        name='domo',
        version= '0.52',
        author_email='hinoglu@gmail.com',
        description='Domo web crawler and parser',
        py_modules=['domo.__init__','domo.services','domo.settings','domo.utils','domo.domo_server',
                   'domo.domo_client','domo.domo_cron' ],
        packages=['domo.interfaces', 'domo.plugins','domo.workers'],
        scripts=['domo/scripts/domo_server.py', 'domo/scripts/domo_client.py'],
        requires=['pyro', 'pycurl', 'lxml', 'cjson', 'multiprocessing', 'sqlalchemy'],
        platforms=['Linux','Unix'],
)
