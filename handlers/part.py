# -*- coding: utf-8 -*-
import datetime
from init import InitHandler
from model.parts import Parts
from model.hanasies import Hanasies
from model.users import Users
from model.likes import Likes
from model.hanasy_bookmarks import HanasyBookmarks
from google.appengine.ext import ndb
from model.notifications import Logs
import re
import logging
import urllib2
from model.notifications import Messages
from google.appengine.api import urlfetch

class PartHandler(InitHandler):
  def __init__(self, request, response):
    InitHandler.__init__(self, request, response)

  def getlist(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    options = {}
    for item in self.arguments:
      options[item] = self.arguments.get(item)

    parts = Parts.getlist(options)

    result['code'] = 200
    result['message'] = 'OK'
    result['Parts'] = self.listToObject(parts)
    return self.createRes(200, result)

  def post(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    try:
      uid = self.get_user().get('uid') if kwargs.get('uid') == 'me' else int(kwargs.get('uid', 0))
      hid = int(kwargs.get('hid'))
      pid = int(kwargs.get('pid', 0))
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

    if not pid:
      # post new part
      arguments = self.arguments
      args_require = ['content', 'image']

      # check parameter validation
      if len(set(arguments) & set(args_require)) == 0:
        result['code'] = 400
        result['message'] = 'bad request'
        return self.createRes(400, result)

      part = Parts(auto_id=True, parent=hanasy.key)

      url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

      video_regex = re.compile('^(?:https?://)?(?:www.)?(?:youtu.be/|youtube.com/(?:embed/|v/|watch\?v=|watch\?.+&v=))((\w|-){11})')

      if self.arguments.get('content'):
        if bool(video_regex.search(self.arguments.get('content'))):
          self.arguments['videoUrl'] = video_regex.findall(self.arguments.get('content'))[0]
          del self.arguments['content']
        elif bool(url_regex.search(self.arguments.get('content'))):
          try:
            response = urllib2.urlopen(self.arguments.get('content'))

            if bool(re.search('image',response.info().getheader('Content-Type'))):
              self.arguments['imageUrl'] = self.arguments.get('content')
              del self.arguments['content']
          except Exception:
            logging.error("image upload error")

      part.set(self.convertRequsetParameter(self.arguments))

      url = '/part/%s/%s/%s' % (author.key.id(), hanasy.key.id(), part.key.id())
      
      #prerender - Hwan Oh 1406290646
      prerenderUrl = "http://api.seo4ajax.com/c674edfc1fb2b6541c18aff2bb3e8264"+url
      prerenderRpc = urlfetch.create_rpc()
      urlfetch.make_fetch_call(prerenderRpc, prerenderUrl);
      #/prerender

      if hanasy.status != 'onair':
        message = u'\'%s\' 하나시의 상태가 변했습니다' % hanasy.title
        url = '/hanasee/%s/%s' % (author.key.id(), hanasy.key.id())

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
      hanasy.partCount = int(hanasy.partCount if hanasy.partCount else 0) + 1
      hanasy.status = 'onair'
      hanasy.put()

      if part:
        result['code'] = 201
        result['message'] = 'OK'
        result['Part'] = part.to_obj()
        return self.createRes(201, result)
      else:
        result['code'] = 400
        result['message'] = 'already exists'
        return self.createRes(400, result)

  def migrate(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    options = {}
    author_email = self.request.get('author')
    hanasy_created = self.request.get('screated')
    pid = 0
    author_info = Users.find(author_email)
    author = author_info.key.get()

    options['author'] = author_info.key
    options['created'] = hanasy_created

    [hanasies, _, _], _ = Hanasies.find(options)
    hanasy = hanasies[0]

    if type(hanasy) == ndb.key.Key:
      result['code'] = 404
      result['message'] = 'not found'
      return self.createRes(404, result)

    if not pid:
      # post new part
      arguments = self.arguments
      args_require = ['content', 'imageUrl', 'image', 'videoUrl']

      # check parameter validation
      if len(set(arguments) & set(args_require)) == 0:
        result['code'] = 400
        result['message'] = 'bad request'
        return self.createRes(400, result)

      part = Parts(auto_id=True, parent=hanasy.key)
      part.set(self.convertRequsetParameter(self.arguments, ['author','screated']))

      hanasy.updated = datetime.datetime.now()
      hanasy.partCount = int(hanasy.partCount if hanasy.partCount else 0) + 1
      hanasy.status = 'onair'
      hanasy.put()

      if part:
        result['code'] = 201
        result['message'] = 'OK'
        result['Part'] = part.to_obj()
        return self.createRes(201, result)
      else:
        result['code'] = 400
        result['message'] = 'already exists'
        return self.createRes(400, result)

  def get(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    try:
      uid = self.get_user().get('uid') if kwargs.get('uid') == 'me' else int(kwargs.get('uid', 0))
      hid = int(kwargs.get('hid'))
      pid = int(kwargs.get('pid', 0))
    except ValueError, e:
      result['code'] = 400
      result['message'] = 'bad request'
      return self.createRes(401, result)

    if kwargs.get('uid') == 'me' and not self.get_user():
      result['code'] = 401
      result['message'] = 'not logged in'
      return self.createRes(401, result)

    author = Users.get(id=uid)
    if type(author) == ndb.key.Key:
      result['code'] = 401
      result['message'] = 'not allowed'
      return self.createRes(401, result)

    hanasy = Hanasies.get(id=hid, parent=author.key)
    if type(hanasy) == ndb.key.Key:
      result['code'] = 404
      result['message'] = 'not found'
      return self.createRes(404, result)

    if not pid:
      # get all parts in a hanasy
      options = {}
      for item in self.arguments:
        options[item] = self.arguments.get(item)

      bFound = None
      if self.get_user():
        mark, bFound = HanasyBookmarks.find(ndb.Key(Users, self.get_user().get('uid')), hanasy.key)
        if bFound:
          options['mark'] = mark.position.get()

      parts = Parts.find(hanasy.key, options)
      like_items = []
      if self.get_user():
        likes = Likes.find(ndb.Key(Users, self.get_user().get('uid')), [part.key for part in parts])
        like_items = [item.target.id() for item in likes]

      result['code'] = 200
      result['message'] = 'OK'
      result['Parts'] = self.listToObject(parts)
      result['Liked'] = like_items
      if bFound:
        result['Marked'] = mark.position.id()
      return self.createRes(200, result)

    else:
      # part detail
      part = Parts.get(id=pid, parent=hanasy.key)
      if type(part) == ndb.key.Key:
        result['code'] = 404
        result['message'] = 'not found'
        return self.createRes(404, result)
      else:
        like_items = []
        bFound = False
        if self.get_user():
          likes = Likes.find(ndb.Key(Users, self.get_user().get('uid')), [part.key])
          like_items = [item.target.id() for item in likes]
          mark, bFound = HanasyBookmarks.find(ndb.Key(Users, self.get_user().get('uid')), hanasy.key)

        result['code'] = 200
        result['message'] = 'OK'
        result['Part'] = part.to_obj()
        result['Liked'] = like_items
        if bFound:
          result['Marked'] = mark.position.id()
        return self.createRes(200, result)

  def delete(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    try:
      uid = self.get_user().get('uid') if kwargs.get('uid') == 'me' else int(kwargs.get('uid', 0))
      hid = int(kwargs.get('hid'))
      pid = int(kwargs.get('pid'))
    except ValueError, e:
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
    hanasy = Hanasies.get(id=hid, parent=author.key)
    if type(hanasy) == ndb.key.Key:
      result['code'] = 404
      result['message'] = 'not found'
      return self.createRes(404, result)

    hanasy.updated = datetime.datetime.now()
    hanasy.partCount = int(hanasy.partCount if hanasy.partCount else 0) - 1
    hanasy.status = 'onair'
    hanasy.put()

    part = Parts.get(id=pid, parent=hanasy.key)

    if type(part) is ndb.key.Key:
      result['code'] = 404
      result['message'] = 'not found'
      return self.createRes(404, result)
    else:
      part.key.delete()
      result['code'] = 200
      result['message'] = 'OK'
      result['Hanasee'] = hanasy.to_obj()
      return self.createRes(200, result)

  def action(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    try:
      uid = self.get_user().get('uid') if kwargs.get('uid') == 'me' else int(kwargs.get('uid', 0))
      hid = int(kwargs.get('hid'))
      pid = int(kwargs.get('pid'))
      action = kwargs.get('action')
    except ValueError, e:
      result['code'] = 400
      result['message'] = 'bad request'
      return self.createRes(401, result)

    if not self.get_user():
      result['code'] = 401
      result['message'] = 'not allowed'
      return self.createRes(401, result)

    user = Users.get(id=self.get_user().get('uid'))
    author = Users.get(id=uid)
    hanasy = Hanasies.get(id=hid, parent=author.key)
    if type(hanasy) == ndb.key.Key:
      result['code'] = 404
      result['message'] = 'not found'
      return self.createRes(404, result)

    part = Parts.get(id=pid, parent=hanasy.key)
    if action in ['like', 'unlike']:
      like = Likes.find(ndb.Key(Users, self.get_user().get('uid')), [part.key])

      if len(like) > 0 and action == 'unlike':
        like[0].key.delete()
      elif len(like) == 0 and action == 'like':
        like = Likes(auto_id=True)
        like.user = user.key
        like.target = part.key
        like.put()

        message = self.arguments.get(
          'message',
          u'%s 님이 당신의 파트를 좋아합니다' % (getattr(user, 'nickname') if user else u'익명'))
        url = self.arguments.get('url', '/part/%s/%s/%s' % (author.key.id(), hanasy.key.id(), part.key.id()))

        if author.key.id() != self.get_user().get('uid'):
          Messages(user=author.key,
            action_user=ndb.Key(Users, self.get_user().get('uid')),
            action='part_like',
            app_name='hanasee',
            settings='myHanaseeReact',
            hanasy=hanasy.key,
            author=author.key,
            part=part.key,
            visible=True,
            message=message,
            url=url).send(['APP','MAIL'])

        if hasattr(part, 'content'):
          message = u'%s 님이 \'%s\' 파트를 좋아합니다' % (getattr(user, 'nickname') if user else u'익명', part.content)
          url = self.arguments.get('url', '/part/%s/%s/%s' % (author.key.id(), hanasy.key.id(), part.key.id()))

          Messages(user=ndb.Key(Users, self.get_user().get('uid')),
            action_user=ndb.Key(Users, self.get_user().get('uid')),
            action='like',
            app_name='hanasee',
            settings='myReact',
            hanasy=hanasy.key,
            author=author.key,
            part=part.key,
            visible=True,
            message=message,
            url=url).send(['SNS'])
      else:
        result['code'] = 500
        result['message'] = 'internal error'
        return self.createRes(500, result)

      part.likeCount = int(part.likeCount if part.likeCount else 0) + (1 if action == 'like' else -1)
      part.put()

      result['code'] = 200
      result['message'] = 'OK'
      result['Part'] = part.to_obj()
      return self.createRes(200, result)
    elif action == 'share':
      part.shareCount = int(part.shareCount if part.shareCount else 0) + 1
      part.put()

      message = self.arguments.get(
        'message',
        u'%s 님이 당신의 파트를 공유했습니다' % (getattr(user, 'nickname') if user else u'익명'))
      url = self.arguments.get('url', '/part/%s/%s/%s' % (author.key.id(), hanasy.key.id(), part.key.id()))

      if self.get_user() and author.key.id() != self.get_user().get('uid'):
        Messages(user=author.key,
          action_user=ndb.Key(Users, self.get_user().get('uid')) if self.get_user() else {},
          action='part_share',
          app_name='hanasee',
          settings='myHanaseeReact',
          hanasy=hanasy.key,
          author=author.key,
          part=part.key,
          visible=True,
          message=message,
          url=url).send(['APP','MAIL'])

      result['code'] = 200
      result['message'] = 'OK'
      result['Part'] = part.to_obj()
      return self.createRes(200, result)

    elif action in ['mark', 'unmark']:
      mark, bFound = HanasyBookmarks.find(user.key, hanasy.key)

      if bFound and action == 'unmark':
        mark.key.delete()
      elif action == 'mark':
        mark.position = Parts.get(id=pid, parent=hanasy.key).key
        mark.put()

        message = self.arguments.get(
          'message',
          u'%s 님이 당신의 하나시에 북마크를 꽂았습니다' % (getattr(user, 'nickname') if user else u'익명'))
        url = self.arguments.get('url', '/hanasee/%s/%s' % (author.key.id(), hanasy.key.id()))

        if author.key.id() != self.get_user().get('uid'):
          Messages(user=author.key,
            action_user=ndb.Key(Users, self.get_user().get('uid')),
            action='part_mark',
            app_name='hanasee',
            settings='myHanaseeReact',
            hanasy=hanasy.key,
            author=author.key,
            part=part.key,
            visible=True,
            message=message,
            url=url).send(['APP','MAIL'])
      else:
        result['code'] = 400
        result['message'] = 'bad request'
        return self.createRes(400, result)

      result['code'] = 200
      result['message'] = 'OK'
      result['Part'] = part.to_obj()
      return self.createRes(200, result)
    elif action in ['addcomment', 'delcomment']:
      if action == 'addcomment':
        message = self.arguments.get(
          'message',
          u'%s 님이 당신의 파트에 댓글을 달았습니다' % (getattr(user, 'nickname') if user else u'익명'))
        url = self.arguments.get('url', '/part/%s/%s/%s' % (author.key.id(), hanasy.key.id(), part.key.id()))

        if self.get_user() and author.key.id() != self.get_user().get('uid'):
          Messages(user=author.key,
            action_user=ndb.Key(Users, self.get_user().get('uid')) if self.get_user() else {},
            action='part_addcomment',
            app_name='hanasee',
            settings='comment',
            hanasy=hanasy.key,
            author=author.key,
            part=part.key,
            visible=True,
            message=message,
            url=url).send(['APP','MAIL'])

      part.commentCount = int(part.commentCount if part.commentCount else 0) + (1 if action == 'addcomment' else -1)
      part.put()

      hanasy.commentCount = int(hanasy.commentCount if hanasy.commentCount else 0) + (1 if action == 'addcomment' else -1)
      hanasy.put()

      result['code'] = 200
      result['message'] = 'OK'
      result['Part'] = part.to_obj()
      return self.createRes(200, result)
    else:
      # invalid action
      result['code'] = 404
      result['message'] = 'not found'
      return self.createRes(404, result)

  def delete_all(self, **kwargs):
    Parts.delete_all()
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
      options['created'] = self.request.get('tcreated')
      parts = Parts.find(hanasy.key, options)
      part = parts[0] if len(parts) > 0 else None

      like = Likes(auto_id=True)
      like.user = user.key
      like.target = part.key
      like.put()

    return self.createRes(200, result)

  def mark_migrate(self, **kwargs):
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
      options['created'] = self.request.get('tcreated')
      parts = Parts.find(hanasy.key, options)
      part = parts[0] if len(parts) > 0 else None

      mark, bFound = HanasyBookmarks.find(user.key, hanasy.key)
      mark.position = part.key
      mark.put()

    return self.createRes(200, result)