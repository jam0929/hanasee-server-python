# -*- coding: utf-8 -*-

#app.js와 동일
#설정들, 라이브러리 로드
#lib
import os
import sys
sys.path.insert(0,os.path.abspath(os.path.dirname(__file__) + '/lib/vendor'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib/custom'))
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/model'))
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/handlers'))
import webapp2
from routes import route_list

reload(sys)
sys.setdefaultencoding('utf-8')

config = {}
config['webapp2_extras.sessions'] = {
  'cookie_name': 'JN',
  'secret_key': 'nuts_at_ajou',
  'session_max_age': 6 * 60 * 60
}
config['webapp2_extras.auth'] = {
  'session_backend': 'nuts_at_ajou'
}

app = webapp2.WSGIApplication(route_list, debug=True, config=config);
