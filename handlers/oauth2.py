# -*- coding: utf-8 -*-
import time
import main
import webapp2
import jinja2
import os
import random
import string
import re
import urllib
import datetime
import logging
from init import InitHandler
from model.users import Users
from model.oauth2_tokens import OAuth2Tokens
from model.oauth2_clients import OAuth2Clients
from google.appengine.ext import ndb

from webapp2_extras import sessions
from webapp2_extras import routes

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader("dialogs"),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def random_char(y):
  return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(y))

class OAuth2Handler(InitHandler):
  # authorize to get a new/existed token
  def __init__(self, request, response):
    InitHandler.__init__(self, request, response)

  def authorize(self):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    arguments = self.arguments
    args_require = ['client_id', 'redirect_uri', 'scope']

    # check parameter validation
    if len(set(arguments) & set(args_require)) != len(args_require):
      result['code'] = 400
      result['message'] = 'bad request'
      return self.createRes(400, result)

    user = self.get_user()
    client = ndb.Key(OAuth2Clients, self.arguments.get('client_id')).get()
    client.name = 'hanasee'
    
    if not user and self.session.get('deviceInfo') is not None and self.session.get('deviceInfo'):
      # device login
      self.session['returnTo'] = self.request.path_qs
      options = self.session.get('deviceInfo')
      
      options['returnTo'] = self.request.path_qs
      options['state'] = self.arguments.get('state')

      template = JINJA_ENVIRONMENT.get_template('device_signin.html')
      return self.response.write(template.render(options))
    elif not user:
      # not logged in, redirect to sign-in
      self.session['returnTo'] = self.request.path_qs
      options = {
        'returnTo': self.request.path_qs,
        'appName': client.name if client else ''
      }
      
      options['state'] = self.arguments.get('state')

      template = JINJA_ENVIRONMENT.get_template('signin.html')
      return self.response.write(template.render(options))

    reqInfo = {}
    for item in [item for item in self.arguments if item not in ['client']]:
      if bool(re.search('\[\d\]', item)):
        if re.sub('\[\d\]', '', item) in reqInfo:
          reqInfo[re.sub('\[\d\]', '', item)].append(self.arguments.get(item))
        else:
          reqInfo[re.sub('\[\d\]', '', item)] = [self.arguments.get(item)]
      elif bool(re.search('\.', item)):
        reqInfo[re.sub('\.', '', item)] = self.arguments.get(item)
      else:
        reqInfo[item] = self.arguments.get(item)

    #reqInfo['redirect_uri'] = urllib.quote_plus(reqInfo['redirect_uri'])

    # check if token exists
    token = OAuth2Tokens.find(ndb.Key(Users, user['uid']), ndb.Key(OAuth2Clients, reqInfo['client_id']))
    # refresh if expired
    if token:
      if hasattr(token, 'expires') and (token.expires < datetime.datetime.now()):
        token = self.grant('refresh', token.to_obj())

      token = token.to_obj()
      options = {
        'access_token': token['access_token'],
        'expire_in': token['expires'],
        'code': 200,
        'message': 'OK',
        'scope': token['scope'],
        'token_type': 'bearer',
        'refresh_token': token['refresh_token'],
        'state': self.arguments.get('state')
      }

      url = self.arguments.get('redirect_uri') + '?'
      url = url + '&'.join(['%s=%s' % (k, v) for k, v in options.items()])
      return self.redirect(str(url))
    else:
      # redirect for authorization
      client = ndb.Key(OAuth2Clients, reqInfo['client_id']).get()
      if not client:
        result['code'] = 400
        result['message'] = 'bad request'
        return self.createRes(400, result)

      # this routine needs 'authorization code', but not now
      self.session['txn'] = reqInfo

      options = {
        'client_name': client.name,
        'state': self.arguments.get('state')
      }

      template = JINJA_ENVIRONMENT.get_template('authorize.html')
      return self.response.write(template.render(options))

  def decision(self):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    txn = self.session.pop('txn', None)

    if txn == None:
      return self.response.write('expired request')

    options = {
      'user_id': self.get_user()['uid'],
      'client_id': txn['client_id'],
      'scope': txn['scope'],
      'status': txn.get('status', None)
    }

    token, bCreated = self.grant('implicit', options)
    token = token.to_obj()

    options = {
      'access_token': token['access_token'],
      'expire_in': token['expires'],
      'code': 200,
      'message': 'OK',
      'scope': token['scope'],
      'token_type': 'bearer',
      'refresh_token': token['refresh_token']
    }

    options['state'] = self.arguments.get('state')

    if txn.get('redirect_uri'):
      url = txn.get('redirect_uri') + '?'
      url = url + '&'.join(['%s=%s' % (k, v) for k, v in options.items()])
      return self.redirect(str(url))
    else:
      result['code'] = 200
      result['message'] = 'OK'
      result['Token'] = token.to_obj()
      return self.createRes(200, result)

  @staticmethod
  def grant(grant_type, options):
    if grant_type == 'implicit':
      user_id = options['user_id']
      client_id = options['client_id']
      scope = options['scope']

      user_key = ndb.Key(Users, user_id)
      client_key = ndb.Key(OAuth2Clients, client_id)
      token = OAuth2Tokens.find(user_key, client_key)
      if token is None:
        return OAuth2Tokens.issue({'scope': scope}, user_key, client_key)
      else:
        return token, False

    elif grant_type == 'refresh':
      if options.get('access_token'):
        old_token = OAuth2Tokens.get_key(options.get('access_token')).get()
        token, bCreated = OAuth2Tokens.refresh(old_token)

      else:
        old_token = OAuth2Tokens.findRefresh(options.get('refresh_token'))
        token, bCreated = OAuth2Tokens.refresh(old_token)
      return token
    else:
      pass
