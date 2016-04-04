# -*- coding: utf-8 -*-
from init import InitHandler
from model.boards import Boards
from model.users import Users
import logging

class BoardHandler(InitHandler):
  def __init__(self, request, response):
    InitHandler.__init__(self, request, response)

  def get(self, **kwargs):
    result = {
      'code'    : 400,
      'message' : 'bad request'
    }

    service = kwargs.get('service')
    type = kwargs.get('type')
    category = self.arguments.get('category')
    owner = None
    if type == 'qna' and self.get_user():
      owner = Users.get(id=self.get_user().get('uid')).key

    result['Boards'] = self.listToObject(Boards.find(service, type, category, owner=owner))
    result['code'] = 200
    result['message'] = 'OK'

    return self.createRes(result['code'], result)

  def post(self, **kwargs):
    result = {
      'code'    : 400,
      'message' : 'bad request'
    }
    
    uid = self.get_user().get('uid') if self.get_user() else None
    if uid is None:
      result['code'] = 401
      result['message'] = 'not authorized'
      return self.createRes(401, result)
    
    if self.arguments.get('type') in ['notice', 'faq'] and self.get_user().get('admin') is None:
      result['code'] = 401
      result['message'] = 'not authorized'
      return self.createRes(401, result)

    owner = Users.get(id=self.get_user().get('uid'))
    board = Boards(auto_id=True)
    for item in self.arguments:
      setattr(board, item, self.arguments.get(item))
    
    board.service = kwargs.get('service')
    board.owner = owner.key
    board.put()

    result['code'] = 200
    result['Board'] = board.to_obj()
    result['message'] = 'OK'

    return self.createRes(result['code'], result)

  def put(self, **kwargs):
    self.post(**kwargs)
    
  def answer(self, **kwargs):
    result = {
      'code'    : 400,
      'message' : 'bad request'
    }
    
    uid = self.get_user().get('uid') if self.get_user() else None
#    if uid is None or self.get_user().get('admin') is None:
#      result['code'] = 401
#      result['message'] = 'not authorized'
#      return self.createRes(401, result)
    
    bid = int(kwargs.get('bid'))
    board = Boards.get(id=bid)
    
    answer = Boards(auto_id=True)
    for item in self.arguments:
      setattr(answer, item, self.arguments.get(item))

    answer.service = kwargs.get('service')
    answer.type = 'qna'
    answer.put()
    
    board.Answer = answer.key
    board.put()    
    
    result['code'] = 200
    result['Board'] = board.to_obj()
    result['message'] = 'OK'

    return self.createRes(result['code'], result)
