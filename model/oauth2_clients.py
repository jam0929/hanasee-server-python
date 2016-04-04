import time, math, random, decimal, md5, string, datetime
from google.appengine.ext import ndb
from model.users import Users
from init import InitModel

def random_char(y):
  return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(y))

class OAuth2Clients(InitModel):
  description = ndb.StringProperty()
  name = ndb.StringProperty()
  owner = ndb.KeyProperty(kind=Users)
  secret = ndb.StringProperty()

  @staticmethod
  def create(name, description, owner):
    # generate key
    unique = "%d%d" % (owner.id(), time.time())
    keymd5 = "8b08d822bba96ffc425c488c60a4fe7b"#md5.md5(unique).hexdigest()#8b08d822bba96ffc425c488c60a4fe7b

    key = ndb.Key(OAuth2Clients, keymd5)
    client = key.get()
    if client is None:
      client = OAuth2Clients(key=key)
      client.name = name
      client.description = description
      client.owner = owner
      client.secret = random_char(32)

      client.put()
      return client, True

    else:
      return client, False

  def to_obj(self, mine = False):
    user = super(OAuth2Clients, self).to_obj(id_name='client_id', except_list=['secret'])