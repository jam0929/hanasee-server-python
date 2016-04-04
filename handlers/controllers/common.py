# -*- coding: utf-8 -*-
import time, datetime, md5
from datetime import timedelta
from model.users import Users
from model.devices import Devices
from model.connections import Connections
from handlers.init import InitHandler
import sys, os, re
from google.appengine.ext import ndb
import jinja2

from authomatic import Authomatic
from authomatic.adapters import Webapp2Adapter

from auth import CONFIG
import logging
from model.notifications import Messages
from model.notifications import Logs

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader("dialogs"),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class CommonHandler(InitHandler):
  def __init__(self, request, response):
    InitHandler.__init__(self, request, response)
    if 'appName' in self.arguments and bool(re.search('\.', self.arguments.get('appName', 'hanasee'))):
      self.arguments['appName'] = re.sub('\.', '', self.arguments.get('appName', 'hanasee'))

  # SIGN IN
  def signin(self, **kwargs):
    logging.error("signin")
    result = {
      'code': 400,
      'message': 'bad request'
    }

    args_signin = ['email', 'password']
    args_device = ['deviceId', 'appName']
    args_oauth = ['type']

    # check parameter validation
    if len(set(self.arguments) & set(args_device)) == len(args_device):
      # device signin
      device_key = ndb.Key('Devices', '%s|%s' % (self.arguments.get('appName'), self.arguments.get('deviceId')))
      device = device_key.get()

      if device and getattr(device, 'user', None) is not None and getattr(device, 'user').get() is not None:
        user = getattr(device, 'user').get()
        self.session['user'] = user.to_obj(mine=True)
        setattr(user, '%s_regid' % self.arguments.get('appName'), device.regId)
        user.put()

        message = '로그인 하셨습니다'
        url = 'http://hanasee.com'
        Messages(user=user.key,
          action_user=user.key,
          action='signin',
          settings='system',
          app_name='hanasee',
          message=message,
          url=url)

        if hasattr(self.session, 'returnTo'):
          return self.redirect(self.session.pop('returnTo'))

        else:
          result['code'] = 200
          result['message'] = 'OK'
          result['User'] = user.to_obj(mine=True)
          return self.createRes(200, result)

      # no information in device
      elif self.arguments.get('returnTo') is not None:
        options = {
          'returnTo': self.arguments.get('returnTo'),
          'appName': self.arguments.get('appName'),
          'state': self.arguments.get('state')
        }

        template = JINJA_ENVIRONMENT.get_template('signin.html')
        return self.response.write(template.render(options))

      else:
        result['code'] = 401
        result['message'] = 'unauthorized'
        return self.createRes(401, result)

    elif len(set(self.arguments) & set(args_signin)) == len(args_signin):
      # email signin
      user = Users.find(self.arguments.get('email'))

      if not user:
        result['code'] = 401
        result['message'] = 'invalid email address' + self.arguments.get('email')
        #return self.createRes(401, result)

      else:
        # check password
        md5password = md5.md5(self.arguments.get('password')).hexdigest()
        if md5password != user.password:
          result['code'] = 401
          result['message'] = 'invalid password'
          #return self.createRes(401, result)

        else:
          # success to login
          # device info
          if ('deviceInfo' in self.session):
            deviceInfo = self.session['deviceInfo']

            # save reg_id in user
            setattr(user, re.sub('\.', '', '%s_regid' % deviceInfo.get('appName')), deviceInfo.get('regId'))
            user.put()

            # save user in device
            device_key = ndb.Key('Devices', '%s|%s' % (deviceInfo.get('appName'), deviceInfo.get('deviceId')))
            device = device_key.get()

            setattr(device, 'user', user.key)
            device.put()

            self.session.pop('deviceInfo')

          message = '로그인 하셨습니다'
          url = 'http://hanasee.com'
          Messages(
            user=user.key,
            action_user=user.key,
            action='signin',
            settings='system',
            app_name='hanasee',
            message=message,
            url=url)

          self.session['user'] = user.to_obj(mine=True)
          result['code'] = 200
          result['message'] = 'OK'

      if result['code'] == 200:
        if self.session.get('returnTo', None):
          returnTo = self.session.pop('returnTo')
          return self.redirect(returnTo)
        else:
          result['code'] = 200
          result['message'] = 'OK'
          result['User'] = user.to_obj(mine=True)
          return self.createRes(200, result)
      else:
        if self.session.get('returnTo', None):
          options = {
            'returnTo': self.session.get('returnTo'),
            'message': result['message'],
            'state': self.session.get('state')
          };

          template = JINJA_ENVIRONMENT.get_template('signin.html')
          return self.response.write(template.render(options))
        else:
          return self.createRes(401, result)
    elif kwargs.get('type'):
      authomatic = Authomatic(config=CONFIG, secret='a-long-secret-string')
      results = authomatic.login(Webapp2Adapter(self), kwargs.get('type'))
      if results:
        if results.error:
          pass
        elif results.user:
          if not results.user.id:
            results.user.update()

          # find existed connection
          connection = Connections.get(id="%s|%s" % (results.provider.name, results.user.id))
          user = None

          if type(connection) == ndb.key.Key:
            connection = Connections(id="%s|%s" % (results.provider.name, results.user.id))

          if connection.user is not None:
            user = connection.user.get()
          elif getattr(results.user, 'email') is not None:
            user = Users.find(results.user.email)

          isNewUser = False

          if user is None:
            user = Users(auto_id=True)
            user.email = getattr(results.user, 'email')
            isNewUser = True

          connection.user = user.key

          if getattr(user, 'nickname') is None:
            if results.provider.name == 'kakao':
              try:
                user.nickname = results.user.data.get(u'properties').get(u'nickname')
              except KeyError, e:
                logging.error('kakao error : ' + e)

                if self.session.get('returnTo', None):
                  template = JINJA_ENVIRONMENT.get_template('signin.html')
                  options = {
                    'returnTo': self.arguments.get('returnTo'),
                    'appName': self.arguments.get('appName'),
                    'state': self.arguments.get('state')
                  }
                  options['message'] = 'internal error'
                  return self.response.write(template.render(options))
                else:
                  result['code'] = 500
                  result['message'] = 'internal error'
                  return self.createRes(500, result)
            else:
              user.nickname = results.user.name

          if getattr(user, 'picture') is None:
            if results.provider.name == 'kakao':
              try:
                user.picture = results.user.data.get(u'properties').get(u'profile_image')
              except KeyError, e:
                logging.error(results.user.data)
            elif results.provider.name == 'fb':
              url = 'https://graph.facebook.com/{}?fields=picture'
              url = url.format(results.user.id)
              response = results.provider.access(url)
              user.picture = response.data.get('picture').get('data').get('url')
            elif results.provider.name == 'tw':
              url = 'https://api.twitter.com/1.1/users/show.json?user_id={}'
              url = url.format(results.user.id)
              response = results.provider.access(url)
              user.picture = response.data.get('profile_image_url')
            elif results.provider.name == 'google':
              user.picture = results.user.picture

          # device info
          if ('deviceInfo' in self.session):
            deviceInfo = self.session['deviceInfo']

            # save reg_id in user
            setattr(user, re.sub('\.', '', '%s_regid' % deviceInfo.get('appName')), deviceInfo.get('regId'))
            user.put()

            # save user in device
            device = ndb.Key(Devices, "%s|%s" % (deviceInfo.get('appName'), deviceInfo.get('deviceId'))).get()
            setattr(device, 'user', user.key)
            device.put()

            self.session.pop('deviceInfo')

          logging.error("qqqq")

          # registered: register message
          if isNewUser:
            logging.error("new user")
            message = '%s님이 하나시를 시작했습니다.' % user.nickname
            url = 'http://hanasee.com'
            Messages(user=user.key,
              action_user=user.key,
              action='regist',
              settings='system',
              app_name='hanasee',
              message=message,
              url=url).send(['MAIL','SNS'])

          # otherwise: sign-in message
          else:
            message = '로그인 하셨습니다'
            url = 'http://hanasee.com'
            Messages(
              user=user.key,
              action_user=user.key,
              action='signin',
              settings='system',
              app_name='hanasee',
              message=message,
              url=url)

          self.session['user'] = user.to_obj(mine=True)

          user.provider = results.provider.name
          setattr(user, results.provider.name, results.provider.credentials.serialize())

          connection.put()
          user.put()

          if self.session.get('returnTo', None):
            returnTo = self.session.pop('returnTo')
            return self.redirect(returnTo)
          else:
            result['code'] = 200
            result['message'] = 'OK'
            result['User'] = user.to_obj(mine=True)
            return self.createRes(200, result)
      else:
        # still processing login
        pass

  # SIGN OUT
  def signout(self, **kwargs):
    #self.session.pop('user', None)
    if self.get_user():
      message = '로그아웃 하셨습니다'
      url = 'http://hanasee.com'
      Messages(user=ndb.Key(Users, self.get_user().get('uid')),
        action_user=ndb.Key(Users, self.get_user().get('uid')),
        action='signout',
        settings='system',
        app_name='hanasee',
        message=message,
        url=url)

    self.session.clear()
    return self.createRes(200, {'message': 'OK'})

  # REGIST
  def regist(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    args_regist = ['email', 'password', 'nickname']

    # check parameter validation
    if len(set(self.arguments) & set(args_regist)) == len(args_regist):
      user = Users.find(self.arguments.get('email'))

      if user:
        result['code'] = 401
        result['message'] = 'already registered'
        #return self.createRes(401, result)

      else:
        # check password
        try:
          md5password = md5.md5(self.arguments.get('password')).hexdigest()
        except UnicodeEncodeError, e:
          logging.error("password = %s" % self.arguments.get('password'))
          return self.createRes(401, result)

        # insert as a new user
        user = Users(auto_id=True)
        user.password = md5password
        user.set(self.convertRequsetParameter(self.arguments, ['password']))

        if ('deviceInfo' in self.session) and ('appName' in self.session['deviceInfo']):
          deviceInfo = self.session['deviceInfo']

          # save reg_id in user
          setattr(user, re.sub('\.', '', '%s_regid' % self.arguments.get('appName')), deviceInfo['regId'])
          user.put()

          # save user in device
          device = ndb.Key(Devices, "%s|%s" % (self.arguments.get('appName'), deviceInfo['deviceId'])).get()
          if device is not None:
            setattr(device, 'user', user.key)
            device.put()

        message = '%s님이 하나시를 시작했습니다.' % user.nickname
        url = 'http://hanasee.com'
        Messages(user=user.key,
          action_user=user.key,
          action='regist',
          settings='system',
          app_name='hanasee',
          message=message,
          url=url).send(['MAIL','SNS'])
        self.session['user'] = user.to_obj(mine=True)
        result['code'] = 200
        result['message'] = 'OK'

      if result['code'] == 200:
        if self.session.get('returnTo', None):
          returnTo = self.session.pop('returnTo')
          return self.redirect(returnTo)
        else:
          result['code'] = 200
          result['message'] = 'OK'
          result['User'] = user.to_obj(mine=True)
          return self.createRes(200, result)
      else:
        if self.session.get('returnTo', None):
          options = {
            'returnTo': self.session.get('returnTo'),
            'message': result['message']
          };

          template = JINJA_ENVIRONMENT.get_template('signin.html')
          return self.response.write(template.render(options))
        else:
          return self.createRes(401, result)

  # DIALOG
  def dialog(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    dialog_list = ['authorize', 'signin', 'find_password', 'reset_password', 'deactivate']
    dialog_type = kwargs.get('type')
    if dialog_type not in dialog_list:
      result['code'] = 400
      result['message'] = 'invalid request'
      return self.createRes(400, result)

    options = {}
    for item in self.arguments:
      options[item] = self.arguments.get(item)

    if self.get_user():
      options['uid'] = self.get_user().get('uid')

    template = JINJA_ENVIRONMENT.get_template(dialog_type + '.html')
    self.response.write(template.render(options))

  # DEVICE
  def devices(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    device_args = ['deviceId', 'appName', 'regId']
    # check parameter validation
    if len(set(self.arguments) & set(device_args)) != len(device_args):
      result['code'] = 400
      result['message'] = 'bad request'
      return self.createRes(400, result)

    if 'deviceInfo' not in self.session:
      self.session['deviceInfo'] = {}

    self.session['deviceInfo'] = {
      'deviceId': self.arguments.get('deviceId'),
      'appName': self.arguments.get('appName'),
      'regId': self.arguments.get('regId')
    }

    device_key = ndb.Key('Devices', '%s|%s' % (self.arguments.get('appName'), self.arguments.get('deviceId')))
    device = device_key.get()

    if device is None:
      device = Devices(key=device_key)
      device.regId = self.arguments.get('regId')
      device.appName = self.arguments.get('appName')
      device.deviceId = self.arguments.get('deviceId')

    elif device.regId != self.arguments.get('regId'):
      device.regId = self.arguments.get('regId')

    if self.get_user():
      user = Users.get(id=self.get_user().get('uid'))
      device.user = user.key
      result['User'] = user.to_obj(mine=True)

    device.put()
    result['code'] = 200
    return self.createRes(200, result)

  # DEVICE
  def devices_migrate(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }
    author = None
    if self.request.get('author', None):
      author = Users.find(self.request.get('author')).key

    arguments = self.request.arguments()
    device_args = ['deviceId', 'appName', 'regId']

    # check parameter validation
    if len(set(arguments) & set(device_args)) != len(device_args):
      result['code'] = 400
      result['message'] = 'bad request'
      return self.createRes(400, result)

    device, bCreated = Devices.get(self.request.get('appName'), self.request.get('deviceId'))
    if not bCreated:
      device.regId = self.request.get('regId')
      if author:
        device.user = author
      device.put()

  def device_delete_all(self, **kwargs):
    Devices.delete_all()

  # DEACTIVATE ACCOUNT
  def deactivate(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    if self.get_user() is None:
      result['code'] = 401
      result['message'] = 'unauthorized'

    elif self.get_user().get('uid') != int(kwargs.get('uid')):
      result['code'] = 401
      result['message'] = 'unauthorized'

    else:
      # get user info
      user = Users.get(id=self.get_user().get('uid'))
      connections = Connections.find(user.key)

      # delete connection info
      for connection in connections:
        connection.key.delete()

      # delete user info
      user.key.delete()
      self.session.clear()

      result['code'] = 200
      result['message'] = 'OK'

    if result['code'] == 200:
      if self.arguments.get('returnTo', None):
        return self.redirect(str(self.arguments.get('returnTo')))
      else:
        result['code'] = 200
        result['message'] = 'OK'
        return self.createRes(200, result)
    else:
      if self.arguments.get('returnTo', None):
        options = {
          'returnTo': self.arguments.get('returnTo'),
          'message': result['message']
        };

        if self.get_user():
          options['uid'] = self.get_user().get('uid')
        template = JINJA_ENVIRONMENT.get_template(self.arguments.get('dialog'))
        return self.response.write(template.render(options))
      else:
        return self.createRes(401, result)


  # NOTIFICATION_LOG
  def notifications(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    options = {}

    if self.get_user():
      uid = self.get_user().get('uid') if kwargs.get('uid', 'me') == 'me' else int(kwargs.get('uid', 0))
      options['app_name'] = kwargs.get('services', None)
      options['user'] = ndb.Key(Users, self.get_user().get('uid'))
      options['cursor'] = self.arguments.get('cursor', None)
      options['limit'] = self.arguments.get('limit', 10)
      notifications, cursor, _ = Logs.find(options)

      unchecked_count = 0

      for notification in notifications:
        if not notification.checked:
          unchecked_count += 1
          notification.checked = True
          notification.put()

      result['code'] = 200
      result['message'] = 'OK'
      result['Notifications'] = self.listToObject(notifications) if len(notifications) > 0 else []
      result['cursor'] = cursor.to_websafe_string() if cursor else None
      result['unchecked'] = unchecked_count
      return self.createRes(200, result)
    else:
      result['code'] = 401
      result['message'] = 'Unauthorized'
      return self.createRes(401, result)
