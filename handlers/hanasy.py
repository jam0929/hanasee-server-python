# -*- coding: utf-8 -*-
from init import InitHandler
from model.hanasies import Hanasies
from model.users import Users
from model.likes import Likes
from model.notifications import Messages
from model.notifications import App_notification
from model.hanasy_current_views import HanasyCurrentViews
from model.hanasy_bookmarks import HanasyBookmarks
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
import re
import time
import datetime
import imghdr,sys
import utils
import logging


class HanasyHandler(InitHandler):
  def __init__(self, request, response):
    InitHandler.__init__(self, request, response)

  def post(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    try:
      uid = self.get_user().get('uid') if kwargs.get('uid', 'me') == 'me' else int(kwargs.get('uid', 0))
      hid = int(kwargs.get('hid', 0))
    except ValueError, e:
      result['code'] = 400
      result['message'] = 'bad request'
      return self.createRes(401, result)
    except AttributeError, e1:
      result['code'] = 400
      result['message'] = 'bad request'
      return self.createRes(401, result)

    if not self.get_user():
      result['code'] = 401
      result['message'] = 'not allowed'
      return self.createRes(401, result)

    if uid and (uid != self.get_user().get('uid')):
      result['code'] = 401
      result['message'] = 'not allowed'
      return self.createRes(401, result)

    author = Users.get(id=uid)
    if type(author) == ndb.key.Key:
      result['code'] = 401
      result['message'] = 'not allowed'
      return self.createRes(401, result)

    if not hid:
      # post new hanasy
      arguments = self.arguments
      args_require = ['title', 'description']

      # check parameter validation
      if len(set(arguments) & set(args_require)) != len(args_require):
        result['code'] = 400
        result['message'] = 'bad request'
        return self.createRes(400, result)

      hanasy = Hanasies(auto_id=True, parent=author.key)
      hanasy.set(self.convertRequsetParameter(self.arguments, ['update']))

      if hanasy:
        message = '하나시 \'%s\'를 작성하셨습니다.' % self.arguments.get('title')
        url = '/hanasee/%s/%s' % (author.key.id(), hanasy.key.id())

        #prerender - Hwan Oh 1406290646
        prerenderUrl = "http://api.seo4ajax.com/c674edfc1fb2b6541c18aff2bb3e8264"+url
        prerenderRpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(prerenderRpc, prerenderUrl);
        #/prerender

        Messages(user=author.key,
          action_user=author.key,
          action='write',
          settings='myHanaseeChange',
          app_name='hanasee',
          hanasy=hanasy.key,
          author=author.key,
          visible=True,
          message=message,
          url=url).send(['MAIL','SNS'])

        result['code'] = 201
        result['message'] = 'OK'
        result['Hanasee'] = hanasy.to_obj()

        return self.createRes(201, result)
      else:
        result['code'] = 500
        result['message'] = 'failed'
        return self.createRes(500, result)

    else:
      # modify hanasy
      hanasy = Hanasies.get(id=hid, parent=author.key)
      if type(hanasy) == ndb.key.Key:
        result['code'] = 404
        result['meessage'] = 'not found'
        return self.createRes(404, result)

      if hanasy.status is not self.arguments.get('status'):
        message = '\'%s\' 하나시의 상태가 변경되었습니다' % (self.arguments.title if getattr(self.arguments,'title',None) else hanasy.title)
        url = self.arguments.get('url', '/hanasee/%s/%s' % (author.key.id(), hanasy.key.id()))
        Messages(user=Hanasies.get_actioned_user(hanasy.key),
          action_user=author.key,
          action='hanasy_status_change',
          settings='favoriteHanaseeNews',
          app_name='hanasee',
          hanasy=hanasy.key,
          author=author.key,
          visible=True,
          message=message,
          url=url).send(['APP','MAIL'])

      hanasy.updated = datetime.datetime.now()
      hanasy.set(self.convertRequsetParameter(self.arguments, ['update']))
      result['code'] = 200
      result['message'] = 'OK'
      result['Hanasee'] = hanasy.to_obj()
      return self.createRes(201, result)

  def put(self, **kwargs):
    self.post(**kwargs)

  def migrate(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    author_email = self.request.get('author')
    hid = 0
    author_info = Users.find(author_email)
    author = author_info.key.get()

    if type(author) == ndb.key.Key:
      result['code'] = 401
      result['message'] = 'not allowed'
      return self.createRes(401, result)

    if not hid:
      # post new hanasy
      arguments = self.arguments
      args_require = ['title', 'description']

      # check parameter validation
      if len(set(arguments) & set(args_require)) != len(args_require):
        result['code'] = 400
        result['message'] = 'bad request'
        return self.createRes(400, result)

      hanasy = Hanasies(auto_id=True, parent=author.key)

      if 'tokCount' in self.arguments:
        self.arguments['partCount'] = self.arguments['tokCount']
        del self.arguments['tokCount']

      hanasy.set(self.convertRequsetParameter(self.arguments, ['author', 'author_id']))

      if hanasy:
        result['code'] = 201
        result['message'] = 'OK'
        result['Hanasee'] = hanasy.to_obj()
        return self.createRes(201, result)
      else:
        result['code'] = 500
        result['message'] = 'failed'
        return self.createRes(500, result)

  def get(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    try:
      uid = self.get_user().get('uid') if kwargs.get('uid') == 'me' else int(kwargs.get('uid', 0))
      hid = int(kwargs.get('hid', 0))
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

    if uid:
      author = Users.get(id=uid)
    else:
      author = None

    # get specific hanasy with key
    if uid and hid:
      if type(author) == ndb.key.Key:
        result['code'] = 404
        result['message'] = 'not found'
        return self.createRes(404, result)

      hanasy = Hanasies.get(id=hid, parent=author.key)
      if type(hanasy) == ndb.key.Key:
        result['code'] = 404
        result['message'] = 'not found'
        return self.createRes(404, result)

      like_items = []
      if self.get_user():
        likes = Likes.find(ndb.Key(Users, self.get_user().get('uid')), [hanasy.key])
        like_items = [item.target.id() for item in likes]

      hanasy.totalViewCount = int(hanasy.totalViewCount if hanasy.totalViewCount else 0) + 1
      hanasy.put()

      if self.get_user() and int(self.get_user().get('uid')) != int(author.key.id()):
        message = '%s님이 당신의 하나시를 보고 있습니다.' % self.get_user().get('nickname') if self.get_user() else '익명'
        url = self.arguments.get('url', '/hanasee/%s/%s' % (author.key.id(), hanasy.key.id()))
        Messages(user=author.key,
          action_user=ndb.Key(Users, self.get_user().get('uid')),
          action='hanasy_view',
          settings='myHanaseeChange',
          app_name='hanasee',
          hanasy=hanasy.key,
          author=author.key,
          visible=True,
          message=message,
          url=url)

      result['code'] = 200
      result['message'] = 'OK'
      result['Hanasee'] = hanasy.to_obj()
      result['Liked'] = like_items
      return self.createRes(200, result)

    # get hanasy list
    else:
      options = {}
      for item in self.arguments:
        options[item] = self.arguments.get(item)

      hcount = None

      if options.get('marked') is not None:
        user = Users.get(id=int(options['marked']))
        marks, cursor, _ = HanasyBookmarks.list(user.key, options)
        hanasies = [mark.target.get() for mark in marks]
      else:
        if author and type(author) != ndb.key.Key:
          options['author'] = author.key
        elif author:
          options['author'] = author

        [hanasies, cursor, _], hcount = Hanasies.find(options)

      result['code'] = 200
      result['message'] = 'OK'
      result['Hanasees'] = self.listToObject(hanasies) if len(hanasies) > 0 else []
      if hcount:
        result['count'] = hcount
      result['cursor'] = cursor.to_websafe_string() if cursor else None
      return self.createRes(200, result)

  def delete(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    try:
      uid = self.get_user().get('uid') if kwargs.get('uid') == 'me' else int(kwargs.get('uid', 0))
      hid = int(kwargs.get('hid', 0))
    except ValueError, e:
      result['code'] = 400
      result['message'] = 'bad request'
      return self.createRes(400, result)

    if not self.get_user():
      result['code'] = 401
      result['message'] = 'not allowed'
      return self.createRes(401, result)

    if uid and (uid != self.get_user().get('uid')):
      result['code'] = 401
      result['message'] = 'not allowed'
      return self.createRes(401, result)

    author = Users.get(id=uid)
    hanasy = Hanasies.get(id=hid, parent=author.key)
    if type(hanasy) == ndb.key.Key:
      result['code'] = 404
      result['message'] = 'not found'
      return self.createRes(404, result)

    message = '하나시 \'%s\'를 삭제하였습니다.' % self.arguments.get('title')
    url = 'http://hanasee.com'
    Messages(user=author.key,
      action_user=author.key,
      action='hanasy_delete',
      settings='myHanaseeChange',
      app_name='hanasee',
      hanasy=hanasy.key,
      author=author.key,
      message=message,
      url=url)

    hanasy.key.delete()
    result['code'] = 200
    result['message'] = 'OK'
    return self.createRes(200, result)

  def action(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    try:
      uid = self.get_user().get('uid') if kwargs.get('uid') == 'me' else int(kwargs.get('uid', 0))
      hid = int(kwargs.get('hid', 0))
    except ValueError, e:
      result['code'] = 400
      result['message'] = 'bad request'
      return self.createRes(400, result)

    action = kwargs.get('action')

    if uid == 'me':
      uid = self.get_user().get('uid')

    author = Users.get(id=uid)
    hanasy = Hanasies.get(id=hid, parent=author.key)
    if type(hanasy) == ndb.key.Key:
      result['code'] = 404
      result['message'] = 'not found'
      return self.createRes(404, result)

    user = Users.get(id=self.get_user().get('uid')) if self.get_user() else None

    if action in ['like', 'unlike']:
      if not self.get_user():
        result['code'] = 401
        result['message'] = 'not allowed'
        return self.createRes(401, result)

      like = Likes.find(user.key, hanasy.key)
      if len(like) > 0 and action == 'unlike':
        like[0].key.delete()
      elif len(like) == 0 and action == 'like':
        message = self.arguments.get(
          'message',
          u'%s 님이 당신의 하나시를 좋아합니다' % (getattr(user, 'nickname') if user else u'익명'))
        url = self.arguments.get('url', '/hanasee/%s/%s' % (author.key.id(), hanasy.key.id()))

        if author.key.id() != self.get_user().get('uid'):
          Messages(user=author.key,
            action_user=ndb.Key(Users, self.get_user().get('uid')),
            action='hanasy_like',
            app_name='hanasee',
            settings='myHanaseeReact',
            hanasy=hanasy.key,
            author=author.key,
            visible=True,
            message=message,
            url=url).send(['APP','MAIL'])

        message = self.arguments.get(
          'message',
          u'%s 님이 \'%s\' 하나시를 좋아합니다' % (getattr(user, 'nickname') if user else u'익명' , hanasy.title))

        Messages(user=ndb.Key(Users, self.get_user().get('uid')),
          action_user=ndb.Key(Users, self.get_user().get('uid')),
          action='like',
          app_name='hanasee',
          settings='myReact',
          hanasy=hanasy.key,
          author=author.key,
          visible=True,
          message=message,
          url=url).send(['SNS'])

        like = Likes(auto_id=True)
        like.user = user.key
        like.target = hanasy.key
        like.put()
      else:
        result['code'] = 500
        result['message'] = 'internal error'
        return self.createRes(500, result)

      hanasy.likeCount = int(hanasy.likeCount if hanasy.likeCount else 0) + (1 if action == 'like' else -1)
      hanasy.put()

      result['code'] = 200
      result['message'] = 'OK'
      result['Hanasee'] = hanasy.to_obj()
      return self.createRes(200, result)
    elif action == 'share':
      message = self.arguments.get(
        'message',
        u'%s 님이 당신의 하나시를 공유했습니다' % (getattr(user, 'nickname') if user else u'익명'))
      url = self.arguments.get('url', '/hanasee/%s/%s' % (author.key.id(), hanasy.key.id()))

      if self.get_user() and author.key.id() != self.get_user().get('uid'):
        Messages(user=author.key,
          action_user=ndb.Key(Users, self.get_user().get('uid')) if self.get_user() else {},
          action='hanasy_share',
          app_name='hanasee',
          settings='myHanaseeReact',
          hanasy=hanasy.key,
          author=author.key,
          visible=True,
          message=message,
          url=url).send(['APP','MAIL'])

      result['code'] = 200
      result['message'] = 'OK'
      result['Hanasee'] = hanasy.to_obj()
      return self.createRes(200, result)
    elif action == 'alive':
      try:
        if self.request.cookies.get('JN') is None:
          self.session['alive'] = True # Fake data to make session

        ssid = self.arguments.get('ssid', self.request.cookies['JN'])
      except KeyError, e1:
        result['code'] = 400
        result['message'] = 'bad request'
        return self.createRes(400, result)
      hcv = HanasyCurrentViews.get(id=hanasy.key.id())
      if type(hcv) == ndb.key.Key:
        hcv = HanasyCurrentViews(id=hanasy.key.id())

      hcv.sessions = set(hcv.sessions + [ssid])
      hcv.hanasy_key = hanasy.key
      hcv.put()

      result['code'] = 200
      result['message'] = 'OK'
      result['Hanasee'] = hanasy.to_obj()
      return self.createRes(200, result)
    elif action == 'notice':
      message = self.arguments.get('message')
      url = self.arguments.get('url', '/hanasee/%s/%s' % (author.key.id(), hanasy.key.id()))

      Messages(user=Hanasies.get_actioned_user(hanasy.key),
        action_user=author.key,
        action='hanasy_notice',
        app_name='hanasee',
        settings='favoriteHanaseeNews',
        hanasy=hanasy.key,
        author=author.key,
        visible=True,
        message=message,
        url=url).send(['APP','MAIL'])

      result['code'] = 200
      result['message'] = 'OK'
      result['Hanasee'] = hanasy.to_obj()
      return self.createRes(200, result)
    elif action in ['addcomment', 'delcomment']:
      notice = utils.notice('ssulit')

      if action == 'addcomment':
        message = self.arguments.get(
          'message',
          u'%s 님이 당신의 하나시에 댓글을 달았습니다' % (getattr(user, 'nickname') if user else u'익명'))
        url = self.arguments.get('url', '/hanasee/%s/%s' % (author.key.id(), hanasy.key.id()))

        if self.get_user() and author.key.id() != self.get_user().get('uid'):
          Messages(user=author.key,
            action_user=ndb.Key(Users, self.get_user().get('uid')) if self.get_user() else {},
            action='hanasy_addcomment',
            settings='comment',
            app_name='hanasee',
            hanasy=hanasy.key,
            author=author.key,
            visible=True,
            message=message,
            url=url).send(['APP','MAIL'])

      hanasy.commentCount = int(hanasy.commentCount if hanasy.commentCount else 0) + (1 if action == 'addcomment' else -1)
      hanasy.put()

      result['code'] = 200
      result['message'] = 'OK'
      result['Hanasee'] = hanasy.to_obj()
      return self.createRes(200, result)
    else:
      # invalid action
      result['code'] = 404
      result['message'] = 'not found'
      return self.createRes(404, result)

  def delete_all(self, **kwargs):
    Hanasies.up()
    self.createRes(200, {'message': 'OK'})

  def like_migrate(self, **kwargs):
    result = {
      'code': 200,
      'message': 'ok'
    }
    author = Users.find(self.request.get('author'))
    user = Users.find(self.request.get('user'))

    options = {}
    options['author'] = author.key
    options['created'] = self.request.get('created')

    [hanasies, _, _], _ = Hanasies.find(options)
    hanasy = hanasies[0] if len(hanasies) > 0 else None

    if hanasy:
      like = Likes(auto_id=True)
      like.user = user.key
      like.target = hanasy.key
      like.put()

    return self.createRes(200, result)

  def summary(self, **kwargs):
    HanasyCurrentViews.summary()

  def noti_test(self, **kwargs):
    result = {
      'code': 200,
      'message': 'ok'
    }

    Messages(test=True)

    return self.createRes(200, result)
