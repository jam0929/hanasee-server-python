import time, datetime
from init import InitModel
from google.appengine.ext import ndb
import re
import logging

class Parts(InitModel):
  created = ndb.DateTimeProperty(indexed=True, default=datetime.datetime.now(), auto_now_add=True)
  likeCount = ndb.IntegerProperty(default=0)
  shareCount = ndb.IntegerProperty(default=0)
  thumbnails = ndb.StringProperty(repeated=True)
  commentCount = ndb.IntegerProperty(default=0)
  content = ndb.TextProperty()

  def to_obj(self):
    return super(Parts, self).to_obj(id_name='tid', parent_name='Hanasee')

  @classmethod
  def getlist(cls, options):
    qry = cls.query()
    if options.get('filter') == 'image':
      qry = qry.order(-cls.created).order(ndb.GenericProperty('image'))
    elif options.get('filter') == 'likeCount':
      dt = datetime.datetime.now() - datetime.timedelta(days=-1)
      qry = qry.order(-cls.likeCount).order(-cls.created)

    limit = int(options.get('limit', 10))
    return qry.fetch(limit)

  @classmethod
  def find(cls, hanasy, options=None):
    qry = cls.query(ancestor = hanasy)

    if qry.count() > 0:
      """
      if options.get('created', None):
        qry = qry.filter(cls.created == datetime.datetime.fromtimestamp(int(options.get('created')) / 1e3))
      """
      order = options.get('order', 'created')
      direction = options.get('direction', 'next')
      limit = int(options.get('limit', 1))
      mark = options.get('mark', None)
      offset = None

      if options.get('offset', None) is not None:
        # make offset
        if direction == 'next':
          if order[0:1] == '-':
            # normal
            offset = datetime.datetime.fromtimestamp(float(options.get('offset')) / 1e3)
          else:
            # +1
            offset = datetime.datetime.fromtimestamp((float(options.get('offset'))+1) / 1e3)
        else:
          if order[0:1] == '-':
            # +1
            offset = datetime.datetime.fromtimestamp((float(options.get('offset'))+1) / 1e3)
          else:
            # normal
            offset = datetime.datetime.fromtimestamp(float(options.get('offset')) / 1e3)
      elif mark is not None:
        offset = mark.created - datetime.timedelta(microseconds=1)

      if order[0:1] == '-':
        if options.get('offset', None) is not None:
          if direction == 'next':
            return qry.filter(cls.created < offset).order(-cls.created).fetch(limit)
          else:
            return qry.filter(cls.created > offset).order(cls.created).fetch(limit)[::-1]
        else:
          return qry.order(-cls.created).fetch(limit)
      else:
        if options.get('offset', None) is not None:
          if direction == 'next':
            return qry.filter(cls.created > offset).order(cls.created).fetch(limit)
          else:
            return qry.filter(cls.created < offset).order(-cls.created).fetch(limit)[::-1]
        else:
          return qry.order(cls.created).fetch(limit)
    else:
      return []
