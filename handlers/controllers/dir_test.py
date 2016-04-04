# -*- coding: utf-8 -*-
import webapp2

class TmpHandler(webapp2.RequestHandler):
  def test(self, **params):
    self.response.write(params)
