# -*- coding: utf-8 -*-
from init import InitHandler
from model.users import Users
from model.oauth2_clients import OAuth2Clients
from google.appengine.ext import ndb

class ClientHandler(InitHandler):
  def __init__(self, request, response):
    InitHandler.__init__(self, request, response)

  def get(self, **kwargs):
    if not self.get_user():
      return self.createRes(401, {'message': 'not logged in'})

    if 'id' in kwargs:
      reqInfo = {
        'id': kwargs.get('id')
      }
      """
      db.clients.find(reqInfo, function(err, client) {
        if (err) { return self.createRes(500, {'message': err }); }
        if (!client) { return self.createRes(404, {'message': err }); }
        return self.createRes(200, client);
      });
      """
    else:
      if 'clients' in self.get_user():
        return self.createRes(200, self.get_user().get('clients'))
      elif self.get_user().get('isDeveloper'):
        return self.createRes(204, {})
      else:
        return self.createRes(401, {'message': 'unauthorized'})

  def put(self, **kwargs):
    self.post(**kwargs)

  def post(self, **kwargs):
    result = {
      'code': 400,
      'message': 'bad request'
    }

    if not self.get_user():
      result['code'] = 401
      result['message'] = 'not logged in'
      return self.createRes(401, result)
    else:#elif self.user.get('isDeveloper'):
      if 'id' in kwargs:
        # update
        pass
      else:
        # insert
        args_require = ['name', 'description']

        # check parameter validation
        if len(set(self.arguments) & set(args_require)) == len(args_require):
          user_key = ndb.Key(Users, self.get_user()['uid'])
          client, created = OAuth2Clients.create(self.arguments.get('name'), self.arguments.get('description'), user_key)
          if created:
            # success
            result['code'] = 201
            result['message'] = 'OK'
            result['client'] = client.to_obj()
            return self.createRes(201, result)
          else:
            # success
            result['code'] = 500
            result['message'] = 'Internal error'
            return self.createRes(500, result)
        else:
          # success
          result['code'] = 400
          result['message'] = 'Bad request'
          return self.createRes(400, result)

  def delete(self, **kwargs):
    print "delete"
    self.createRes(200, {'message': 'OK'});
