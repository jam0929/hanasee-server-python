import time, datetime
from init import InitModel
from model.users import Users
from google.appengine.ext import ndb
import re

class Likes(InitModel):
  user = ndb.KeyProperty(kind=Users, required=True)
  target = ndb.KeyProperty(required=True) # User can like 'anything'

  def to_obj(self):
    return super(Likes, self).to_obj(id_name='target', except_list=['user', 'target'])

  @classmethod
  def find(cls, user_key, target_key):
    if target_key:
      if not isinstance(target_key, list):
        target_key = [target_key]

      qry = cls.query()
      if user_key is not None:
        qry = qry.filter(cls.user == user_key)
      qry = qry.filter(cls.target.IN(target_key))

      result = qry.fetch()
      return result
    else:
      return []
