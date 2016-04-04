from init import InitModel
from model.hanasies import Hanasies
from google.appengine.ext import ndb

class HanasyCurrentViews(InitModel):
  sessions = ndb.TextProperty(repeated=True)
  hanasy_key = ndb.KeyProperty(kind=Hanasies)
  lastCount = ndb.IntegerProperty(default=0)

  @classmethod
  def summary(cls):
    result = cls.query().fetch()
    for item in result:
      hanasy = item.hanasy_key.get()
      
      if hanasy:
        hanasy.viewCount = len(item.sessions)
        hanasy.put()

      if len(item.sessions) == 0:
        item.key.delete()
      else:
        item.lastCount = len(item.sessions)
        item.sessions[:] = []
        item.put()
    return None