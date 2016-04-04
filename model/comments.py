import time, datetime
from init import InitModel
from google.appengine.ext import ndb
from model.users import Users
import json
import re
from google.appengine.datastore.datastore_query import Cursor

class Comments(InitModel):
  Author = ndb.KeyProperty(kind=Users)
  created = ndb.DateTimeProperty(default=datetime.datetime.now(), auto_now_add=True)
  url = ndb.StringProperty(required=True)
  likeCount = ndb.IntegerProperty(default=0)

  @classmethod
  def find(cls, url, options=None):
    cursor = Cursor(urlsafe=options.get('cursor'))
    qry = cls.query()
    qry = qry.filter(cls.url == url)
    qry = qry.order(-cls.created)

    if options.get('filter'):
      filter = json.loads(options.get('filter'))
      for key, value in filter.items():
        qry = qry.filter(ndb.GenericProperty(key) == value)

    if cursor:
      return qry.fetch_page(int(options.get('limit', 20)), start_cursor=cursor)
    else:
      return qry.fetch_page(int(options.get('limit', 20)))

  def to_obj(self):
    return super(Comments, self).to_obj(id_name='cid')

  @classmethod
  def _post_delete_hook(cls, key, future):
    comments = cls.query(ndb.GenericProperty('owned') == key).fetch(keys_only=True)
    ndb.delete_multi(comments)
