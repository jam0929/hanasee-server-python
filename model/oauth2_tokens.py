import time, math, random, decimal, md5, datetime, re, string
from google.appengine.ext import ndb
from init import InitModel
from model.users import Users
from model.oauth2_clients import OAuth2Clients

def random_char(y):
  return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(y))

class OAuth2Tokens(InitModel):
  client = ndb.KeyProperty(kind=OAuth2Clients, required=True)
  expires = ndb.DateTimeProperty(default=datetime.datetime.now() + datetime.timedelta(days=1), required=True)
  refresh_token = ndb.StringProperty()
  token_type = ndb.StringProperty(default='bearer')
  scope = ndb.StringProperty(required=True)
  user = ndb.KeyProperty(kind=Users, required=True, indexed=True)

  def to_obj(self):
    return super(OAuth2Tokens, self).to_obj(id_name='access_token')

  @staticmethod
  @ndb.transactional
  def get_owner(keyString, reqInfo):
    key = ndb.Key(OAuth2Tokens, keyString)
    token = key.get()
    if user is None:
      token = OAuth2Tokens(key=key)
      token.put()
      return token.user

  @staticmethod
  def get_key(key):
    return ndb.Key(OAuth2Tokens, key)

  @staticmethod
  def get(key):
    token = key.get()
    if token is None:
      token = OAuth2Tokens(key=key)
      return token, True
    else:
      return token, False

  @staticmethod
  def set(reqInfo):
    if not keyString:
      keyString = random_char(16)

  @staticmethod
  def find(user_key, client_key):
    qry = OAuth2Tokens.query()
    result = qry.filter(OAuth2Tokens.client == client_key).filter(OAuth2Tokens.user == user_key).fetch()
    return result[0] if len(result) > 0 else None
    
  @staticmethod
  def findRefresh(refresh_token):
    qry = OAuth2Tokens.query()
    result = qry.filter(OAuth2Tokens.refresh_token == refresh_token).fetch()
    return result[0] if len(result) > 0 else None

  @staticmethod
  def refresh(token):
    user_key = getattr(token, 'user')
    client_key = getattr(token, 'client')
    refresh_token = getattr(token, 'refresh_token')
    scope = getattr(token, 'scope')

    token.key.delete()

    return OAuth2Tokens.issue({'scope': scope}, user_key, client_key, refresh_token)

  @staticmethod
  def issue(reqInfo, user_key, client_key, refresh_token=None):
    token = OAuth2Tokens.find(user_key, client_key)

    if token is None:
      keyString = random_char(16)
      key = ndb.Key(OAuth2Tokens, keyString)
      token = OAuth2Tokens(key=key)
      token.user = user_key
      token.client = client_key
      token.refresh_token = refresh_token if refresh_token else random_char(16)

      for item in reqInfo.keys():
        if not hasattr(token, item):
          setattr(token, item, reqInfo[item])
        elif type(getattr(token, item)) == type(0):
          setattr(token, item, (int)(reqInfo.get(item)))
        elif type(getattr(token, item)) == datetime.datetime:
          setattr(token, item, datetime.datetime.fromtimestamp(int(reqInfo.get(item)) / 1e3))
        else:
          setattr(token, item, reqInfo.get(item))

      token.put()
      return token, True
    else:
      return token, False

