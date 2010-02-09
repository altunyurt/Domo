# ~*~ coding:utf-8 ~*~

from datetime import datetime
from domo import settings
from domo.utils import normalize_price
from sqlalchemy import (create_engine, Table, MetaData, String, TEXT, DATETIME,
                        Column, Integer, ForeignKey, Unicode, CHAR)
from sqlalchemy.exceptions import InvalidRequestError
from sqlalchemy.orm import mapper, sessionmaker, relation, backref, scoped_session
from sqlalchemy.pool import SingletonThreadPool
import traceback

engine = create_engine(settings.MANAGEMENT_DATABASE, 
                           echo=settings.MANAGEMENT_DATABASE_VERBOSE,
                           pool_recycle=settings.MANAGEMENT_DATABASE_RECYCLE,
                           convert_unicode=True, encoding='utf-8',
                           poolclass=SingletonThreadPool)
metadata = MetaData(bind=engine)

Session = sessionmaker(bind=engine, autoflush=True)


'''
    Profile: configuration profile for each seed or seed group.
    Configuration profile is an extendible xml (json?) data that is unified 
    with given name and seed data

'''
profile = Table('profile', metadata,
                Column('id', Integer, primary_key=True),
                Column('name', Unicode(100), nullable=False, index=True),
                Column('configuration', Unicode(10000), nullable=False,
                       index=False),
)

'''
    Job: every job is based on a profile instance.
'''

job = Table('job', metadata, 
            Column('id', Integer, primary_key=True),
            Column('profile_id', Integer, ForeignKey('profile.id'),
                   nullable=False),
            Column('name', Unicode(120), nullable=False, index=True),
            Column('stts', CHAR(1), nullable=False),
            Column('start_date', DATETIME, nullable=False, default=datetime.now),
            Column('end_date', DATETIME, nullable=True),
)

'''
    index data regarding to the archive format
'''

index = Table('arcindex', metadata, 
             Column('id', Integer, primary_key=True),
             Column('filename', Unicode(500), nullable=False, index=True),
             Column('timestamp', Integer, nullable=False, index=True),
             Column('url', Unicode(500), nullable=False, index=True),
             Column('offset', Integer, nullable=False),
)

JOB_STATUS = {'p': 'paused', 
              'r': 'running',
              'e': 'ended',
              'k': 'killed'}


class Profile(object):
    def __init__(self, name):
        ''' profile objects are identified by names '''
        self.name = name

class Job(object):
    def __init__(self, name, status):
        self.name = name
        self.stts = status

    def _set_status(self, status):
        for key, val in JOB_STATUS.items():
            if status == val:
                self.stts = key

    def _get_status(self):
        return JOB_STATUS.get(self.stts)

    status = property(_get_status, _set_status)

class Index(object):
    def __init__(self, filename, timestamp, url, offset):
        self.filename = filename
        self.timestamp = timestamp
        self.url = url
        self.offset = offset

class Log(object):
    ''' abstract logger class'''
    pass

mapper(Profile, profile, properties={ 'jobs': relation(Job, 
        primaryjoin=profile.c.id==job.c.profile_id, foreign_keys=[job.c.profile_id])})
mapper(Job, job)
mapper(Index, index)
metadata.create_all()
