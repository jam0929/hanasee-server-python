# -*- coding: utf-8 -*-
from init import InitHandler
from model.channels import Channels

class ChannelHandler(InitHandler):
  def __init__(self, request, response):
    InitHandler.__init__(self, request, response)

  def get(self, **kwargs):
    result = {
      'code'    : 400,
      'message' : 'bad request'
    }

    result['Channels'] = self.listToObject(Channels.get(self.request.get('country')))
    result['code'] = 200
    result['message'] = 'OK'

    return self.createRes(result['code'], result)

  def post(self, **kwargs):
    result = {
      'code'    : 400,
      'message' : 'bad request'
    }

    #ADMIN CHECK

    name = self.request.get('name')
    order = self.request.get('order')

    result['channel'] = Channels.set(name,order).to_obj()
    result['code'] = 200
    result['message'] = 'OK'

    return self.createRes(result['code'], result)
