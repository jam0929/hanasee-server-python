import time, datetime
from init import InitModel
from model.users import Users
from google.appengine.ext import ndb

class Connections(InitModel):
  user = ndb.KeyProperty(kind=Users, required=True)

  @classmethod
  def find(cls, user_key):
    qry = cls.query()
    qry = qry.filter(cls.user == user_key)
    result = qry.fetch()
    
    return result