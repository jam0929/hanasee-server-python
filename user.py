import main
import session, webapp2

class Login(main.BaseHandler):
  def get(self):
    self.session['foo'] = 'bar'
  def post(self):
    foo = self.session.get('foo')
    self.response.write(foo)

application = webapp2.WSGIApplication([
    ('/user/.*', Login),
], debug=True)
