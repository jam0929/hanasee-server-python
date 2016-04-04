# -*- coding: utf-8 -*-

import webapp2
from webapp2_extras import routes
from handlers import *
from handlers.controllers import *

route_list = []

_base = [
  webapp2.Route('<:.*>', methods=['OPTIONS'], handler=init.InitHandler, handler_method='options'),
  webapp2.Route('/', handler=dir_test.TmpHandler, handler_method='test', methods=['GET']),
]
route_list += _base

_common = [
  webapp2.Route('/clients', handler=client.ClientHandler, methods=['GET','POST','PUT']),
  webapp2.Route('/clients/<id>', handler=client.ClientHandler, methods=['GET','POST','PUT','DELETE']),

  webapp2.Route('/comments/<url>', handler=comment.CommentHandler, methods=['GET','POST','PUT']),
  webapp2.Route('/comments/<url>/<cid>', handler=comment.CommentHandler, methods=['POST','PUT','DELETE']),
  webapp2.Route('/comments/<url>/<cid>/<action>', handler=comment.CommentHandler, methods=['POST','PUT',], handler_method='action'),

  webapp2.Route('/users', handler=user.UserHandler, methods=['GET', 'POST']),
  webapp2.Route('/users/<uid>', handler=user.UserHandler, methods=['GET','POST','PUT','DELETE']),
  webapp2.Route('/users/<uid>/<attribute>', handler=user.UserHandler, methods=['POST','PUT']),
  webapp2.Route('/users/reset', handler=user.UserHandler, methods=['POST','PUT'], handler_method='reset'),

  webapp2.Route('/devices', handler=common.CommonHandler, methods=['POST','PUT'], handler_method='devices'),

  webapp2.Route('/oauth2/authorize', handler=oauth2.OAuth2Handler, methods=['GET'], handler_method='authorize'),
  webapp2.Route('/dialog/authorize', handler=oauth2.OAuth2Handler, methods=['GET'], handler_method='authorize'),
  webapp2.Route('/oauth2/decision', handler=oauth2.OAuth2Handler, methods=['POST'], handler_method='decision'),

  webapp2.Route('/auth/facebook', handler=dir_test.TmpHandler, methods=['GET']),
  webapp2.Route('/auth/facebook/callback', handler=dir_test.TmpHandler, methods=['GET']),
  webapp2.Route('/auth/facebook/callback/<encoded>', handler=dir_test.TmpHandler, methods=['GET']),

  webapp2.Route('/<service>/boards/<type>', handler=board.BoardHandler, methods=['GET','POST','PUT']),
  webapp2.Route('/<service>/boards/qna/<bid>', handler=board.BoardHandler, methods=['POST','PUT'], handler_method='answer'),
  webapp2.Route('/<service>/version', handler=dir_test.TmpHandler, methods=['GET']),
  webapp2.Route('/<service>/notifications', handler=common.CommonHandler, methods=['GET'], handler_method='notifications'),

  webapp2.Route('/notifications', handler=noticenter.NotiCenterHandler, methods=['GET']),
  webapp2.Route('/notifications/count', handler=noticenter.NotiCenterHandler, methods=['GET'], handler_method='get_count'),
  webapp2.Route('/notifications/setting', handler=noticenter.NotiSettingHandler, methods=['GET', 'POST', 'PUT']),
  webapp2.Route('/notifications/worker', handler=noticenter.NotiCenterHandler, methods=['POST'], handler_method='worker')
]

route_list += _common

_controllers = [
  webapp2.Route('/signin', handler=common.CommonHandler, methods=['POST','PUT'], handler_method='signin'),
  webapp2.Route('/signin/<type>', handler=common.CommonHandler, methods=['GET'], handler_method='signin'),
  webapp2.Route('/signout', handler=common.CommonHandler, methods=['POST','PUT'], handler_method='signout'),
  webapp2.Route('/regist', handler=common.CommonHandler, methods=['POST','PUT'], handler_method='regist'),
  webapp2.Route('/notification', handler=dir_test.TmpHandler, methods=['POST','PUT']),
  webapp2.Route('/deactivate/<uid>', handler=common.CommonHandler, methods=['POST', 'PUT'], handler_method='deactivate')
]
route_list += _controllers

_hanasy = [
  #CRONJOB
  webapp2.Route('/hanasee/hanasees/summary', handler=hanasy.HanasyHandler, methods=['GET','POST','PUT'], handler_method='summary'),

  #CHANNEL
  webapp2.Route('/hanasee/hanasees/ch', handler=channel.ChannelHandler, methods=['GET']),
  webapp2.Route('/hanasee/hanasees/channels', handler=channel.ChannelHandler, methods=['GET', 'POST']),

  #HANASY
  webapp2.Route('/hanasee/hanasees', handler=hanasy.HanasyHandler, methods=['GET','POST','PUT']),
  webapp2.Route('/hanasee/hanasees/<uid>', handler=hanasy.HanasyHandler, methods=['GET']),
  webapp2.Route('/hanasee/hanasees/<uid>/<hid>', handler=hanasy.HanasyHandler, methods=['GET','POST','PUT','DELETE']),
  webapp2.Route('/hanasee/hanaseesnoti', handler=hanasy.HanasyHandler, methods=['GET'], handler_method='noti_test'),

  #PART
  webapp2.Route('/hanasee/hanasees/<uid>/<hid>/parts', handler=part.PartHandler, methods=['GET','POST','PUT']),
  webapp2.Route('/hanasee/hanasees/<uid>/<hid>/parts/<pid>', handler=part.PartHandler, methods=['GET','DELETE']),

  webapp2.Route('/hanasee/hanasees/<uid>/<hid>/<action>', handler=hanasy.HanasyHandler, methods=['POST','PUT'], handler_method='action'),
  webapp2.Route('/hanasee/hanasees/<uid>/<hid>/parts/<pid>/<action>', handler=part.PartHandler, methods=['POST','PUT'], handler_method='action'),
  webapp2.Route('/hanasee/parts', handler=part.PartHandler, methods=['GET'], handler_method='getlist')
]

route_list += _hanasy

_dialogs = [
  webapp2.Route('/dialog/<type>', handler=common.CommonHandler, methods=['GET'], handler_method='dialog'),
]
"""
server.get('/dialog/signin', common.dialogs.signin);
server.get('/dialog/signout', common.dialogs.signout);
server.get('/dialog/regist', login.ensureLoggedOut({ redirectTo: '/dialog/signout' }), common.dialogs.regist);
server.get('/dialog/client/create', login.ensureLoggedIn({ redirectTo: '/dialog/signin' }), common.dialogs.createClient);

server.get('/dialog/reset_password', common.dialogs.reset_password);
server.get('/dialog/find_password', common.dialogs.find_password);

// oauth: authorization
server.get('/dialog/authorize',
  login.ensureLoggedIn({ redirectTo: '/dialog/signin', setReturnTo: true }), middleware.oauth2.authorization);
server.post('/dialog/authorize/decision',
  login.ensureLoggedIn({ redirectTo: '/dialog/signin', setReturnTo: true }), middleware.oauth2.decision);
"""
route_list += _dialogs

"""
_images = [
  webapp2.Route('/images/<blobId>', handler=image.ImageHandler, methods=['GET'])
]

route_list += _images
_test = [
  webapp2.Route('/users', handler=user.UserHandler, methods=['DELETE']),
  webapp2.Route('/parts', handler=part.PartHandler, methods=['DELETE'], handler_method='delete_all'),
  webapp2.Route('/hanasies', handler=hanasy.HanasyHandler, methods=['DELETE'], handler_method='delete_all'),
  webapp2.Route('/devices', handler=common.CommonHandler, methods=['DELETE'], handler_method='device_delete_all'),
  webapp2.Route('/devices/migrate', handler=common.CommonHandler, methods=['POST','PUT'], handler_method='devices_migrate'),
  webapp2.Route('/hanasy/hanasies/migrate', handler=hanasy.HanasyHandler, methods=['POST'], handler_method='migrate'),
  webapp2.Route('/hanasy/parts/migrate', handler=part.PartHandler, methods=['POST'], handler_method='migrate'),
  webapp2.Route('/hanasy/like/migrate/hanasies', handler=hanasy.HanasyHandler, methods=['POST'], handler_method='like_migrate'),
  webapp2.Route('/hanasy/like/migrate/parts', handler=part.PartHandler, methods=['POST'], handler_method='like_migrate'),
  webapp2.Route('/hanasy/mark/migrate', handler=part.PartHandler, methods=['POST'], handler_method='mark_migrate'),
]

route_list += _test
"""