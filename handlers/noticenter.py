# -*- coding: utf-8 -*-
from init import InitHandler
from model.users import Users
from model.notifications import Logs
from model.notifications import NotiCenter, Notification_Settings, Messages
from datetime import datetime
from datetime import timedelta
from google.appengine.ext import ndb
import logging
import yaml

class NotiCenterHandler(InitHandler):
  def cronjob(self, **kwargs):
    #logs = Logs.find(datetime.now() - timedelta(minutes=-5))
    logs = Logs.find(None)

    for log in logs:
      if log.action is 'hanasy_view':
        noti = NotiCenter.get(id="%s|%s" % (log.action, log.hanasy.id()))
        logging.error(log)

  def get(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    options = {}

    uid = self.get_user().get('uid') if kwargs.get('uid', 'me') == 'me' and self.get_user() else int(kwargs.get('uid', 0))

    if uid == 0:
      result['code'] = 401
      result['message'] = 'unauthorized'
      return self.createRes(401, result)

    #options['app_name'] = kwargs.get('services', None)
    options['user'] = ndb.Key(Users, uid)
    options['cursor'] = self.request.get('cursor', None)
    options['limit'] = self.request.get('limit', 10)
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

  def get_count(self, **kwargs):
    # TODO: return unread notification count
    result = {
      'code': 400,
      'message': 'bad request'
    }

    options = {}

    uid = self.get_user().get('uid') if kwargs.get('uid', 'me') == 'me' else int(kwargs.get('uid', 0))
    options['user'] = ndb.Key(Users, self.get_user().get('uid'))
    options['limit'] = self.request.get('limit', 20)
    notifications, cursor, _ = Logs.find(options)

    unchecked_count = 0

    for notification in notifications:
      if not notification.checked:
        unchecked_count += 1

    result['code'] = 200
    result['message'] = 'OK'
    result['unchecked'] = unchecked_count
    return self.createRes(200, result)
    
  def worker(self, **kwargs):
    #added from oh
    o = yaml.load(self.arguments.get('object'))
    m = yaml.load(self.arguments.get('methods'))
    Messages.worker(o, m)

class NotiSettingHandler(InitHandler):
  def get(self, **kwargs):
    result = {
      'code'    : 400,
      'message' : 'bad request'
    }

    uid = self.get_user().get('uid')
    user = Users.get(id=uid)

    setting = Notification_Settings.find(user.key)
    if setting is None:
      setting = Notification_Settings(auto_id=True, parent=user.key)
      setting.put()

    result['code'] = 200
    result['message'] = 'OK'
    result['Setting'] = setting.to_obj()

    return self.createRes(200, result)

  def put(self, **kwargs):
    self.post(**kwargs)

  def post(self, **kwargs):
    result = {
      'code'    : 400,
      'message' : 'bad request'
    }

    uid = self.get_user().get('uid')
    user = Users.get(id=uid)

    setting = Notification_Settings.find(user.key)
    if setting is None:
      setting = Notification_Settings(auto_id=True, parent=user.key)

    for item in self.arguments:
      setattr(setting, item, self.arguments.get(item))

    setting.put()

    result['code'] = 200
    result['message'] = 'OK'
    result['Setting'] = setting.to_obj()

    return self.createRes(200, result)
