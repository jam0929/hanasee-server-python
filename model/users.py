import time, math, random, decimal, md5, datetime
from init import InitModel
from notifications import Notification_Settings
from google.appengine.ext import ndb
import logging

class Users(InitModel):
  email = ndb.StringProperty(indexed=True)
  nickname = ndb.StringProperty(required=True, indexed=True)
  password = ndb.StringProperty()
  picture = ndb.StringProperty()
  created = ndb.DateTimeProperty(default=datetime.datetime.now(), auto_now_add=True)
  provider = ndb.StringProperty(default='JN')

  @classmethod
  def find(cls, email):
    result = cls.query(cls.email == email).fetch()
    return result[0] if len(result) > 0 else None

  @staticmethod
  def regist(email, reqInfo):
    user = Users.find(email)
    if user is None:
      uid = str(decimal.Decimal(math.floor(time.time() * 100 * 100) + math.floor(random.random() * 100)))
      user = Users(id=int(uid))
      for item in reqInfo.keys():
        if item == 'password':
          setattr(user, item, md5.md5(reqInfo.get(item)).hexdigest())
        else:
          setattr(user, item, reqInfo.get(item))

      user.put()

      del user.password
      return user, True
    return user, False

  def to_obj(self, mine = False):
    user = super(Users, self).to_obj(id_name='uid', except_list=['password','device','hanasee_regid','ssulit_regid'])

    if mine:
      return user
    else:
      partial = {
        'uid': user.get('uid'),
        'nickname': user.get('nickname'),
        'language': user.get('language'),
        'picture': user.get('picture')
      }

      return partial

  def _post_put_hook(self, future):
    notisetting = Notification_Settings(auto_id=True, parent=self.key)
    notisetting.put()

  @classmethod
  def delete_all(cls):
    users = cls.query().fetch()
    for user in users:
      if not hasattr(user, 'provider'):
        user.provider = 'JN'
        user.put()