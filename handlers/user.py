# -*- coding: utf-8 -*-
import time
import datetime
from datetime import timedelta
import sys
import os
import re
import md5
from google.appengine.ext import ndb
import utils
from model.users import Users
from model.connections import Connections
from init import InitHandler
from model.devices import Devices
from oauth2 import OAuth2Handler
from model.oauth2_tokens import OAuth2Tokens
import logging
import jinja2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader("dialogs"),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class UserHandler(InitHandler):
  def __init__(self, request, response):
    InitHandler.__init__(self, request, response)

  # GET USERS (MY INFO)
  def get(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }
    
    # token refresh
    if kwargs.get('uid') == 'me' and self.arguments.get('refresh_token'):
      token = OAuth2Handler.grant('refresh', {'refresh_token': self.arguments.get('refresh_token')})

      result['code'] = 200
      result['message'] = 'OK'
      result['User'] = token.user.get().to_obj(mine = True)
      result['Token'] = token.to_obj()
      return self.createRes(200, result)

    try:
      uid = self.get_user().get('uid') if kwargs.get('uid') == 'me' else int(kwargs.get('uid', 0))
    except ValueError, e:
      result['code'] = 400
      result['message'] = 'bad request'
      return self.createRes(400, result)
    except AttributeError, e1:
      result['code'] = 400
      result['message'] = 'bad request'
      return self.createRes(400, result)

    if kwargs.get('uid') == 'me' and not self.get_user():
      result['code'] = 401
      result['message'] = 'not logged in'
      return self.createRes(401, result)

    user = Users.get(id=int(uid))
    me = self.get_user().get('uid') if self.get_user() else None
    if type(user) == ndb.key.Key:
      # cannot find user
      result['code'] = 401
      result['message'] = 'invalid uid'
      return self.createRes(401, result)
    elif user.key.id() == me:
      result['code'] = 200
      result['message'] = 'OK'
      result['User'] = user.to_obj(mine = True)
      return self.createRes(200, result)
    else:
      result['code'] = 200
      result['message'] = 'OK'
      result['User'] = user.to_obj()
      return self.createRes(200, result)

  # GET USERS (MY INFO)
  def list(self, **kwargs):
    pass

  # SET USERS (ADD/UPDATE)
  def regist(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    # check arguments
    if not (self.arguments.get('email') and self.arguments.get('password') and self.arguments.get('nickname')):
      result['code'] = 400
      result['message'] = 'bad request'
      return self.createRes(400, result)

    else:
      user, created = Users.regist(self.arguments.get('email'), self.arguments)
      if not created:
        result['code'] = 400
        result['message'] = 'already exists'
        return self.createRes(400, result)

      else:
        result['code'] = 201
        result['message'] = 'OK'
        result['User'] = user.to_obj(mine=True)
        return self.createRes(201, result)

  def put(self, **kwargs):
    print "put"
    self.post(**kwargs)

  def post(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }
    
    # update user info
    if kwargs.get('uid'):
      if self.get_user() is None:
        result['code'] = 401
        result['message'] = 'unauthorized'
      else:
        
        uid = self.get_user().get('uid')
  
        if kwargs.get('uid') != 'me' and uid != int(kwargs.get('uid')):
          result['code'] = 400
          result['message'] = 'already exists'
          return self.createRes(400, result)
        
        reqInfo = self.arguments
          
        # get user info
        user = Users.get(id=uid)
        if type(user) == ndb.key.Key:
          result['code'] = 400
          result['message'] = 'bad request'
        
        else:
          # using API, user can modify nickname and picture
          available_list = ['nickname', 'picture', 'hanasee', 'language'] + [kwargs.get('attribute')]
    
          reqInfo = []
          for field in self.arguments:
            if field in available_list:
              if hasattr(self.arguments[field], 'FieldStorageClass'):
                dtCreated = datetime.datetime.now()
                filename = "%d" % (time.mktime(dtCreated.timetuple())*1e3 + dtCreated.microsecond/1e3)
                
                image_url = self.create_file(self.arguments.get(field).value, filename, self.arguments.get(field).type)
                setattr(user, field, image_url)
              elif field == 'password':
                if user.password == md5.md5(self.arguments.get('old_password')).hexdigest():
                  setattr(user, field, md5.md5(self.arguments.get('password')).hexdigest())
                else:
                  result['code'] = 401
                  result['message'] = 'invalid password'
              else:
                setattr(user, field, self.arguments.get(field))
          
          if result['code'] != 401:
            user.put()
            
            result['code'] = 200
            result['message'] = 'OK'
            result['User'] = user.to_obj(mine = True)
        
    else:
      arguments = self.arguments
      args_regist = ['email', 'password', 'nickname']
  
      # check parameter validation
      if len(set(arguments) & set(args_regist)) == len(args_regist):
        user = Users.find(self.request.get('email'))
  
        if user:
          result['code'] = 401
          result['message'] = 'already registered'
          #return self.createRes(401, result)
  
        else:
          # check password
          #md5password = md5.md5(self.arguments.get('password')).hexdigest()
  
          # insert as a new user
          user = Users(auto_id=True)
          #user.password = md5password
          user.password = self.arguments.get('password')
          user.set(self.convertRequsetParameter(self.arguments, ['password']))
  
          if ('deviceInfo' in self.session) and (appName in self.session['deviceInfo']):
            deviceInfo = self.session['deviceInfo'][self.request.get('appName')]
  
            # save reg_id in user
            setattr(user, re.sub('\.', '', self.request.get('appName')), deviceInfo['regId'])
            user.put()
  
            # save user in device
            device = ndb.Key(Devices, "%s|%s" % (self.request.get('appName'), deviceInfo['deviceId'])).get()
            setattr(device, 'user', user.key)
            device.put()
  
          self.session['user'] = user.to_obj(mine=True)
          result['code'] = 200
          result['message'] = 'OK'
  
    if result['code'] == 200:
      if self.arguments.get('returnTo', None):
        return self.redirect(str(self.arguments.get('returnTo')))
      else:
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

  def post_backup(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    reqInfo = {}
    for item in self.arguments:
      if bool(re.search('\[\d\]', item)):
        if re.sub('\[\d\]', '', item) in reqInfo:
          reqInfo[re.sub('\[\d\]', '', item)].append(self.arguments.get(item))
        else:
          reqInfo[re.sub('\[\d\]', '', item)] = [self.arguments.get(item)]
      elif bool(re.search('\.', item)):
        reqInfo[re.sub('\.', '', item)] = self.arguments.get(item)
      else:
        reqInfo[item] = self.arguments.get(item)

    Users.set(reqInfo)
    return self.createRes(200, {'me':'O'})

    redirect_uri = self.session['returnTo'] if self.session and self.session['returnTo'] else self.arguments.get('returnTo')
    redirect_uri = redirect_uri + '&from=regist' if redirect_uri else null
    del self.session['returnTo']

    if not kwargs.get('id'):
      if not self.arguments.get('email') or not self.arguments.get('password'):
        return self.createRes(400, {'message': 'missing parameter'})

      current = time.time()
      id = (current * 100) + Math.floor(Math.random() * 100)
      key = {
        'id': id.toString(),
        'email': self.arguments.get('email')
      }

      if self.arguments.get('nickname'):
        key['nickname'] = self.arguments.get('nickname')

      reqInfo = {}
      for item in self.arguments:
        reqInfo[item] = self.argum.get(item);

      """
      db.users.regist(key, reqInfo, function(err, user) {
        if err == 'already exists':
          return res.render('regist', {'message': '이메일 또는 닉네임을 사용할 수 없습니다.'})
          return self.createRes(409, {'message': err})
        elif err:
          return res.render('regist', {'message': '알 수 없는 에러가 발생했습니다. 다시 시도해주세요.'})
          return self.createRes(500, {'message': err})
        elif not user:
          return res.render('regist', {'message': err})
          return self.createRes(500, {'message': 'unknown error'})

        del user.password
        self.logIn(user, function(err) {
          if self.session.deviceInfo:
            for (appName in self.session.deviceInfo):
              if self.session.deviceInfo[appName] !== user[appName]:
                regId = {}
                regId[appName] = self.session.deviceInfo[appName].regId
                keyDevice = {'appName': appName, 'deviceId': self.session.deviceInfo[appName].deviceId}
                db.users.update({'id': user.id}, regId)
                db.devices.update(keyDevice, {'user_id': user.id})

          if redirect_uri:
            return res.redirect(redirect_uri)
          else:
            result['code'] = 200
            result['message'] = 'OK'
            result['User'] = user
            return self.createRes(200, user)
        })
      })
      """
    else:
      # modify my userinfo
      if kwargs.get('id') == 'me' or kwargs.get('id') == self.get_user().get('id'):
        if not self.get_user():
          return self.createRes(401, {'message': 'not logged in'})

        key = {
          id: self.get_user().get('id')
        }

        reqInfo = {}
        for item in self.arguments:
          reqInfo[item] = self.arguments.get(item);

        # cannot modify id
        del reqInfo['id']
        del reqInfo['email']
        del reqInfo['kakao']


        if kwargs.get('attribute') == 'connection':
          if not reqInfo.get('connectionProvider'):
            return self.createRes(400, {'message': 'missing parameter'})

          unique = reqInfo.get('connectionProvider')[0:3]+self.get_user().get('id')[2:4]+str(time.time())
          md5.md5(unique).hexdigest()

          reqInfo[reqInfo['connectionProvider']] = connectionKey
          del reqInfo['connectionProvider']
        """
        db.users.update(key, reqInfo, function(err, user) {
          del user['password']
          del user['kakao']
          del user['facebook']

          self.logIn(user, function(err) {
            if kwargs.get('attribute') == 'connection':
              user['connectionKey'] = connectionKey

            return self.createRes(200, user)
          })
        })
        """
      elif self.get_user().get('id') != kwargs.get('id'):
        return self.createRes(401, {'message': 'cannot modify others'})

  # DEL USERS
  def delete(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }
    
    # check user validation
    if self.get_user() is None:
      result['code'] = 401
      result['message'] = 'unauthorized'
      return self.createRes(401, result)
    
    uid = int(kwargs.get('uid'))
    if uid != self.get_user().get('uid'):
      result['code'] = 401
      result['message'] = 'unauthorized'
      return self.createRes(401, result)
    
    # get user info
    user = Users.get(id=uid)
    connections = Connections.find(user.key)
    
    # delete connection info
    for connection in connections:
      connection.key.delete()
    
    # delete user info
    user.key.delete()
    self.session.clear()
    
    result['code'] = 200
    result['message'] = 'OK'
    return self.createRes(200, result)

  def reset(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    if not self.arguments.get('email') or not self.arguments.get('returnTo'):
      return self.createRes(400, {'message': 'invalid request'})

