import time, datetime
from init import InitModel
from model.users import Users
from model.parts import Parts
from google.appengine.ext import ndb
import re
from google.appengine.datastore.datastore_query import Cursor

class HanasyBookmarks(InitModel):
  user = ndb.KeyProperty(kind=Users, required=True)
  target = ndb.KeyProperty(required=True) # User can like 'anything'
  position = ndb.KeyProperty(kind=Parts)
  created = ndb.DateTimeProperty(default=datetime.datetime.now(), auto_now_add=True)

  @classmethod
  def find(cls, user_key, target_key):
    result = HanasyBookmarks.query()
    result = result.filter(cls.user == user_key)
    result = result.filter(cls.target == target_key)
    result = result.fetch(limit=1)
    return (result[0], True) if len(result) > 0 else (cls(user=user_key, target=target_key), False)

  @classmethod
  def list(cls, user_key, options):
    qry = cls.query()
    cursor = Cursor(urlsafe=options.get('cursor'))

    # filters
    qry = qry.filter(cls.user == user_key)
    
    # order
    if qry.count() > 0:
      order = options.get('order', None)
      if order == 'created':
        order = cls.created
      else:
        order = -cls.created
      qry = qry.order(order)

    if cursor:
      return qry.fetch_page(int(options.get('limit', 20)), start_cursor=cursor)
    else:
      return qry.fetch_page(int(options.get('limit', 20)))
    return (result[0], True) if len(result) > 0 else (HanasyBookmarks(user=user_key, target=target_key), False)

  @staticmethod
  def find_v2(target_key):
    result = HanasyBookmarks.query()
    result = result.filter(HanasyBookmarks.target == target_key)
    result = result.fetch()
    return result

