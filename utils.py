# -*- coding: utf-8 -*-
from gcm import GCM

api_keys = {
  'ssulit': 'ssulit'
}

class notice(object):
  def __init__(self, *args):
    self.api_key = api_keys[args[0]]

  def sendNotice(self, reg_ids, message, url):
#    api_key = 'ssulit'
    gcm = GCM(self.api_key)
    data = {
      'url': url,
      'message': message
    }

    response = gcm.json_request(registration_ids=reg_ids, data=data)

    # Extra arguments
    res = gcm.json_request(
        registration_ids=reg_ids, data=data
    )

    return res
