# -*- coding: utf-8 -*-

import time, datetime
from init import InitModel
from google.appengine.ext import ndb
from gcm import GCM
from authomatic import Authomatic
from handlers.controllers.auth import CONFIG
from google.appengine.api import urlfetch
from google.appengine.api import mail
import logging
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.api import taskqueue
import json
import jinja2
import yaml

api_keys = {
  'ssulit': 'AIzaSyCk9ozGirgmZ3Iamgfoht5E3GUb2lLwdbY',
  'hanasee': 'AIzaSyBfBMHu78cdBzu-nLpthPPHf9fTkxpbsyI'
}

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader("dialogs"),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class App_notification(object):
  def __init__(self, *args):
    self.api_key = api_keys[args[0]]

  def sendNotice(self, reg_ids, message, url):
    gcm = GCM(self.api_key)
    data = {
      'url': url,
      'message': message
    }

    response = gcm.json_request(registration_ids=reg_ids, data=data)

    # Extra arguments
    res = gcm.json_request(
      registration_ids=reg_ids, data=data
    )

    return res

class Logs(InitModel):
  # save for each actions
  user = ndb.KeyProperty(kind='Users')
  action = ndb.StringProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)
  app_name = ndb.StringProperty()
  checked = ndb.BooleanProperty(default=False)
  visible = ndb.BooleanProperty(default=False)
  url = ndb.StringProperty(default='http://hanasee.com')
  """
  user = ndb.KeyProperty(kind=Users) # user who actioned
  target = ndb.KeyProperty() # target that was acted by user (hanasy/ part/ comment)
  receiver = ndb.KeyProperty(kind=Users, required=True)
  action = ndb.StringProperty()
  message = ndb.StringProperty()
  url = ndb.StringProperty()
  appname = ndb.StringProperty()
  created = ndb.DateTimeProperty(default=datetime.datetime.now(), auto_now_add=True)
  """

  @classmethod
  def find(cls, options):
    user = options.get('user')
    cursor = Cursor(urlsafe=options.get('cursor'))
    limit = options.get('limit', 10)
    app_name = options.get('app_name', None)

    qry = cls.query(cls.user == user)
    qry = qry.filter(cls.visible == True)

    if app_name is not None:
      qry = qry.filter(cls.app_name == app_name)

    qry = qry.order(-cls.created)

    if cursor:
      return qry.fetch_page(int(limit), start_cursor=cursor)
    else:
      return qry.fetch_page(int(limit))

  def to_obj(self):
    return super(Logs, self).to_obj(except_list=['author', 'hanasy', 'user', 'visible', 'part'])

class Messages(object):
  def __init__(self, *args, **kwargs):
    if kwargs.get('test'):
      self.send(['MAIL'])
    else:
      for key, value in kwargs.iteritems():
        setattr(self, key, value)

      users = kwargs.get('user')
      logs = []

      if not isinstance(users, list):
        users = [users]

      for user in users:
        log = Logs()
        log.user = user
        for key, value in kwargs.iteritems():
          if key is 'user':
            continue
          setattr(log, key, value)
        logs.append(log)

      ndb.put_multi(logs)

  # send to user
  def send(self, methods):
   taskqueue.add(url='/notifications/worker', params={'object': yaml.dump(self), 'methods': yaml.dump(methods)})

  @classmethod
  def worker(cls, self, methods):
    users = self.user

    if not isinstance(users, list):
      users = [users.get()]
    else:
      users = [user.get() for user in users]

    for method in methods:
      if method == 'APP':
        reg_ids = []
        for user in users:
          if getattr(user, '%s_regid' % self.app_name, None):
            reg_ids.append(getattr(user, '%s_regid' % self.app_name))

        if len(reg_ids) > 0:
          App_notification(self.app_name).sendNotice(reg_ids, self.message, self.url if self.url.startswith('http') else 'http://hanasee.com%s' % self.url)
      elif method == 'MAIL':
        for user in users:
          if type(user) == ndb.key.Key or getattr(user, 'email', None) is None:
            pass
          elif mail.is_email_valid(user.email):
            user_address = user.email
            sender_address = "Hanasee <nuts@jumpingnuts.com>"
            subject = '[Hanasee] %s' % self.message

            body = """
하나시(Hanasee)에서 알려드립니다. \n\n
%s \n\n
바로가기 : %s \n\n
항상 저희 점핑너츠의 하나시(Hanasee)를 이용해주시는 유저분들께 감사드립니다.
""" % (self.message, self.url if self.url.startswith('http') else 'http://hanasee.com%s' % self.url)

            options = {}
            options['username'] = user.nickname
            options['uid'] = user.key.id()
            options['picture'] = user.picture
            options['message'] = self.message
            options['url'] = self.url if self.url.startswith('http') else 'http://hanasee.com%s' % self.url
            options['email'] = user.email

            template = JINJA_ENVIRONMENT.get_template('email.html')
            html = template.render(options)

            mail.send_mail(sender_address, user_address, subject, body, html=html)
      elif method == 'SNS':
        authomatic = Authomatic(config=CONFIG, secret='a-long-secret-string')
        for user in users:
          if type(user) == ndb.key.Key:
            pass
          elif getattr(user, 'fb', None):
            token = user.fb
            """
            if self.action == 'regist' or self.action == 'write':
              url = 'https://graph.facebook.com/me/feed'
              body = u'message=%s&link=%s&caption=HANASEE' % (self.message, self.url if self.url.startswith('http') else 'http://hanasee.com%s' % self.url)
            else:
              url = 'https://graph.facebook.com/v2.0/me/og.likes'
              body = u'message=%s&object=%s' % (self.message, self.url if self.url.startswith('http') else 'http://hanasee.com%s' % self.url)
            """

            url = 'https://graph.facebook.com/me/feed'
            body = u'message=%s&link=%s' % (self.message, self.url if self.url.startswith('http') else 'http://hanasee.com%s' % self.url)

            authomatic.access(token, url, method='POST', body=body)
          elif getattr(user, 'tw', None):
            token = user.tw

            url = 'https://api.twitter.com/1.1/statuses/update.json'
            #body = u'status=%s' % (self.message + self.url if self.url.startswith('http') else 'http://hanasee.com%s' % self.url)
            body = self.message + self.url if self.url.startswith('http') else 'http://hanasee.com%s' % self.url

            authomatic.access(token, url, method='POST', params=dict(status=body))
            ''''
            authomatic.access(token,
                                         url='https://api.twitter.com/1.1/statuses/update.json',
                                         params=dict(status=(self.message + self.url if self.url.startswith('http') else 'http://hanasee.com%s' % self.url)),
                                         method='POST')
            '''
          elif getattr(user, 'kakao', None):
            token = user.kakao

            self.url = self.url if self.url.startswith('http') else 'http://hanasee.com%s' % self.url

            urlInfo = {}
            urlInfo['url'] = self.url
            urlInfo['host'] = 'hanasee.com'

            if getattr(self, 'part', None):
              part = self.part.get()
              urlInfo['title'] = part.content
            elif getattr(self, 'hanasy', None):
              hanasy = self.hanasy.get()
              urlInfo['title'] = hanasy.title
              urlInfo['description'] = hanasy.description
              """
              images = []
              i = 0;
              for image in hanasy.images:
                if i > 2:
                  break
                images.append(image)
                i = i+1

              if len(images) > 0:
                urlInfo['image'] = images
              """
            else:
              urlInfo['title'] = 'Hanasee'
              #urlInfo['image'] = ['https://lh5.ggpht.com/-8H5uPC3vLUCBhTLW0gWZQEMBQLWxsQ7mrkKbSEtvWl97OkPjoYxShx7zUKYICn19CA=w300-rw']

            urlInfo = json.dumps(urlInfo)
            url = 'https://kapi.kakao.com/v1/api/story/post/link'
            body = u'link_info=%s&content=%s&android_exec_param=url=%s' % (urlInfo, self.message, self.url)

            authomatic.access(token, url, method='POST', body=body)
          elif getattr(user, 'google', None):
            pass
        pass
      else:
        pass



class NotiCenter(InitModel):
  user = ndb.KeyProperty(kind='Users')
  action = ndb.StringProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)
  app_name = ndb.StringProperty()
  alarm = ndb.BooleanProperty(default=False)
  message = ndb.StringProperty()
  count = ndb.IntegerProperty(default=1)

  @classmethod
  def find(cls, user, cursor):
    qry = cls.query(cls.user == user)
    qry = qry.order(-cls.created)

    if cursor:
      return qry.fetch_page(int(options.get('limit', 10)), start_cursor=cursor)
    else:
      return qry.fetch_page(int(options.get('limit', 10)))

class Notification_Settings(InitModel):
  # owner : parent
  # 댓글 TTX
  comment_mail = ndb.StringProperty(default='T')
  comment_push = ndb.StringProperty(default='T')
  comment_social = ndb.StringProperty(default='X')

  # 내 하나시 반응 TTF
  myHanaseeReact_mail = ndb.StringProperty(default='T')
  myHanaseeReact_push = ndb.StringProperty(default='T')
  myHanaseeReact_social = ndb.StringProperty(default='F')

  # 내 하나시 조회 TTX
  myHanaseeView_mail = ndb.StringProperty(default='T')
  myHanaseeView_push = ndb.StringProperty(default='T')
  myHanaseeView_social = ndb.StringProperty(default='X')

  # 반응한 하나시 소식 TTX
  favoriteHanaseeNews_mail = ndb.StringProperty(default='T')
  favoriteHanaseeNews_push = ndb.StringProperty(default='T')
  favoriteHanaseeNews_social = ndb.StringProperty(default='X')

  # 반응한 하나시 구독 TFX
  favoriteHanaseeAction_mail = ndb.StringProperty(default='T')
  favoriteHanaseeAction_push = ndb.StringProperty(default='F')
  favoriteHanaseeAction_social = ndb.StringProperty(default='X')

  # 내 반응 TFX
  myReact_mail = ndb.StringProperty(default='T')
  myReact_push = ndb.StringProperty(default='F')
  myReact_social = ndb.StringProperty(default='X')

  # 내 하나시 변경 TFF
  myHanaseeChange_mail = ndb.StringProperty(default='T')
  myHanaseeChange_push = ndb.StringProperty(default='F')
  myHanaseeChange_social = ndb.StringProperty(default='F')

  # 내 상태 변경 TFX
  myStatusChange_mail = ndb.StringProperty(default='T')
  myStatusChange_push = ndb.StringProperty(default='F')
  myStatusChange_social = ndb.StringProperty(default='X')

  @classmethod
  def find(cls, user_key):
    result = cls.query(ancestor = user_key).fetch()
    return result[0] if len(result) > 0 else None

  def to_obj(self):
    return super(Notification_Settings, self).to_obj(parent_name='User')
