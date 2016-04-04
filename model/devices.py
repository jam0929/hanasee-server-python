from init import InitModel
import time, math, random, decimal, md5, datetime
from google.appengine.ext import ndb
from model.users import Users

class Devices(InitModel):
  appName = ndb.StringProperty(required=True)
  deviceId = ndb.StringProperty(required=True)
  regId = ndb.StringProperty(required=True)
  created = ndb.DateTimeProperty(default=datetime.datetime.now(), auto_now=True)
  user = ndb.KeyProperty(kind=Users)
