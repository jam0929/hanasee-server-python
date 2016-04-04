from init import InitModel
from google.appengine.ext import ndb
import datetime

class Boards(InitModel):
  service = ndb.StringProperty(required=True)
  type = ndb.StringProperty(required=True)
  content = ndb.StringProperty(required=True)
  created = ndb.DateTimeProperty(default=datetime.datetime.now(), auto_now_add=True)

  @classmethod
  def find(cls, service, type, category=None, owner=None):
    query = cls.query()
      
    query = query.filter(cls.service.IN([service, 'Common']))
    query = query.filter(cls.type == type)
    if category is not None:
      query = query.filter(ndb.StringProperty('category') == category)
      
    if owner is not None:
      query = query.filter(ndb.KeyProperty('owner') == owner)

    query = query.order(-cls.created)
    return query.fetch()

  def to_obj(self):
    return super(Boards, self).to_obj(id_name='bid')
