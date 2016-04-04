# -*- coding: utf-8 -*-
from __future__ import with_statement
from google.appengine.ext import blobstore
from google.appengine.api import images
import cloudstorage as gcs
import webapp2
import json
import session
import re
import urllib2
import datetime
import time
import logging
from model.oauth2_tokens import OAuth2Tokens

class InitHandler(session.SessionHandler):
  def __init__(self, request, response):
    self.initialize(request, response)

    self.arguments = {}

    for key in request.GET.keys():
      self.arguments[key] = request.GET.getall(key) if len(request.GET.getall(key)) > 1 else request.GET.get(key)

    if len(request.POST.items()) > 0:
      for key in request.POST.keys():
        self.arguments[key] = request.POST.getall(key) if len(request.POST.getall(key)) > 1 else request.POST.get(key)
    elif request.body:
      try:
        self.arguments.update(json.loads(request.body))
      except ValueError, e:
        logging.error(e)

    token_key = self.arguments.get('access_token', None)

    if token_key:
      key = OAuth2Tokens.get_key(token_key)
      token = key.get()

      if token and token.user:
        try:
          self.user = token.user.get().to_obj()
        except AttributeError, e:
          self.user = None

  def createRes(self, code, res):
    self.response.headers['Access-Control-Allow-Credentials'] = 'true'
    self.response.headers['Access-Control-Allow-Origin'] = self.request.headers.get('origin') if self.request.headers.get('origin') else '*'
    self.response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    self.response.headers['Access-Control-Allow-Headers'] = 'X-CSRF-Token, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
    self.response.headers['P3P:CP'] = 'IDC DSP COR ADM DEVi TAIi PSA PSD IVAi IVDi CONi HIS OUR IND CNT'
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.status_int = code
    self.response.write(json.dumps(res, encoding='utf-8'))

  # Send 'OK' Whenever 'OPTIONS' come
  def options(self, *args, **kwargs):
    result = {
      'code': 200,
      'message': 'OK'
    }

    self.createRes(200, result)

  def get_user(self):
    user = getattr(self, 'user', None)
    return user if user else self.session.get('user', None)

  def listToObject(self, list):
    result = []

    for object in list:
      try:
        result.append(object.to_obj())
      except AttributeError, e:
        pass

    return result

  def convertRequsetParameter(self, request, except_list=[]):
    reqInfo = {}
    except_list = list(set(except_list + ['access_token', 'token_type', 'key']))

    for item in self.arguments:
      if item in except_list:
        pass
      elif bool(re.search('\.', item)):
        reqInfo[re.sub('\.', '', item)] = self.arguments.get(item)
      else:
        reqInfo[item] = self.arguments.get(item)

    thumbnails = []
    og_img = None

    for item in reqInfo:
      if hasattr(reqInfo[item][0] if isinstance(reqInfo[item], list) else reqInfo[item], 'FieldStorageClass'):
        if not isinstance(reqInfo[item], list):
          reqInfo[item] = [reqInfo[item]]

        x = 0
        for image in reqInfo[item]:
          dtCreated = datetime.datetime.now()
          filename = "%d" % (time.mktime(dtCreated.timetuple())*1e3 + dtCreated.microsecond/1e3)
          image_url = self.create_file(image.value, filename, image.type)
          reqInfo[item][x] = image_url
          _image = images.Image(image.value)
          width = _image.width
          height = _image.height

          """
          if x is 0:
            og_img =
          """

          if width < 501:
            pass
          elif width >= height:
            image_url = image_url+'=s500'
          else:
            ratio = 500.0/width
            height = int(height * ratio)
            if height <= 1600:
              image_url = image_url+'=s'+str(height)

          thumbnails.append(image_url)
          x += 1

    if thumbnails:
      reqInfo['thumbnails'] = thumbnails
      #reqInfo['og_img'] = og_img

    update = request.get('update')

    if update:
      update = json.loads(update)

      for item in update:
        if update[item]:
          if isinstance(item, unicode):
            _item = str(item)
          else:
            _item = item

          if _item == 'deleteItem':
            #TODO image delete
            continue

          x = 0
          for image in update[item]:
            if _item in reqInfo:
              reqInfo[_item].insert(x, image)
            else:
              reqInfo[_item] = [image]
            x += 1

    return reqInfo

  def create_file(self, image, filename, type):
    bucket = '/hanasy/images/'
    filename = bucket+filename

    with gcs.open(filename, 'w', type) as f:
      f.write(image)

    filename = urllib2.quote('/gs'+filename)

    bkey = blobstore.create_gs_key(filename)

    return images.get_serving_url(bkey)
