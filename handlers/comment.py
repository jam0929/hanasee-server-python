# -*- coding: utf-8 -*-
import json
import time
import re
import urllib
import operator
from init import InitHandler
from model.likes import Likes
from model.users import Users
from model.comments import Comments
from google.appengine.ext import ndb

class CommentHandler(InitHandler):
  def __init__(self, request, response):
    InitHandler.__init__(self, request, response)

  def _removeOverhead(self, url):
    decoded_url = urllib.unquote(url).decode('utf8')
    return re.sub(r'http[s]*:\/\/[w]*\.*', r'', decoded_url)

  def get(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    url = self._removeOverhead(kwargs.get('url'))

    options = {}
    for item in self.arguments:
      options[item] = self.arguments.get(item)

    comments, cursor, _ = Comments.find(url, options)

    like_items = []
    if self.get_user():
      likes = Likes.find(ndb.Key(Users, self.get_user().get('uid')), [comment.key for comment in comments])
      like_items = [item.target.id() for item in likes]

    result['code'] = 200
    result['message'] = 'OK'
    result['Comments'] = self.listToObject(comments)
    result['Liked'] = like_items
    result['cursor'] = cursor.to_websafe_string() if cursor else None
    return self.createRes(200, result)

  def post(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    reqInfo = self.convertRequsetParameter(self.arguments, ['owned', 'access_token'])

    url = self._removeOverhead(kwargs.get('url'))
    cid = int(kwargs.get('cid', 0))
    user = self.get_user()
    password = self.arguments.get('password', None)

    reqInfo['Author'] = ndb.Key(Users, user.get('uid')) if user else None
    reqInfo['url'] = url
    if hasattr(reqInfo, 'key'):
      del reqInfo['key']

    if cid:
      comment = Comments.get(id=cid)
      if type(comment) == ndb.key.Key:
        result['code'] = 404
        result['message'] = 'not found'
        return self.createRes(404, result)
      elif password != comment.get('password'):
        result['code'] = 401
        result['message'] = 'not allowed'
        return self.createRes(401, result)
    elif user is None and password is None:
        result['code'] = 400
        result['message'] = 'bad request'
        return self.createRes(400, result)
    elif self.arguments.get('owned'):
      comment = Comments(auto_id=True)
      owned = Comments.get(id=int(self.arguments.get('owned')))
      reqInfo['owned'] = owned.key.id() if type(owned) != ndb.key.Key else comment.key.id()
    else:
      comment = Comments(auto_id=True)
      reqInfo['owned'] = comment.key.id()

    comment.set(reqInfo)

    result['code'] = 200
    result['message'] = 'OK'
    result['Comments'] = comment.to_obj()
    return self.createRes(200, result)

  def delete(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    cid = int(kwargs.get('cid', 0))
    comment = Comments.get(id=cid)
    if type(comment) == ndb.key.Key:
      result['code'] = 404
      result['message'] = 'not found'
      return self.createRes(404, result)
    else:
      comment.key.delete()
      result['code'] = 200
      result['message'] = 'OK'
      return self.createRes(200, result)

  def action(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    cid = int(kwargs.get('cid', 0))
    url = kwargs.get('url')
    action = kwargs.get('action')

    if not self.get_user():
      result['code'] = 401
      result['message'] = 'not allowed'
      return self.createRes(401, result)

    user = Users.get(id=self.get_user().get('uid'))
    comment = Comments.get(id=cid)

    if action in ['like', 'unlike']:
      like = Likes.find(ndb.Key(Users, self.get_user().get('uid')), [comment.key])
      if len(like) > 0 and action == 'unlike':
        like[0].key.delete()
      elif len(like) == 0 and action == 'like':
        like = Likes(auto_id=True)
        like.user = user.key
        like.target = comment.key
        like.put()
      else:
        result['code'] = 500
        result['message'] = 'internal error'
        return self.createRes(500, result)

      comment.likeCount = int(comment.likeCount if comment.likeCount else 0) + (1 if action == 'like' else -1)
      comment.put()

      result['code'] = 200
      result['message'] = 'OK'
      result['Comment'] = comment.to_obj()
      return self.createRes(200, result)

