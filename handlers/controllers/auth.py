
from authomatic.providers import oauth2, oauth1, gaeopenid
import authomatic


CONFIG = {
  'tw': { # Your internal provider name

    # Provider class
    'class_': oauth1.Twitter,
  
    # Twitter is an AuthorizationProvider so we need to set several other properties too:
    'consumer_key': 'COBPpUYrZvvPcmpWHmiFWD2Xm',
    'consumer_secret': 'RqgsDNWdrxfklLFkWHNHwMp70Y0dpMahAgOwdbZ1iRqOgvwZ1G',
    'id': authomatic.provider_id()
  },

  'kakao': { # Your internal provider name

    # Provider class
    'class_': oauth2.Kakao,
    'id': authomatic.provider_id(),
    'consumer_key': '37b8d7bd27a5547aa74149ae15c329e1',
    'consumer_secret': ''
  },

  'fb': {
    'class_': oauth2.Facebook,
    
    # Facebook is AuthorizationProvider too.
    'consumer_key': '264001293758406',
    'consumer_secret': '7882ca0b7313eb8961dd0024f22ec18a',
    'id': authomatic.provider_id(),
    
    # We need the "publish_stream" scope to post to users timeline,
    # the "offline_access" scope to be able to refresh credentials,
    # and the other scopes to get user info.
    'scope': ['publish_stream', 'offline_access', 'user_about_me', 'email'],
  },
  
  'google': {
    'class_': oauth2.Google,
    'consumer_key':'264752365528-1qfjo3boh8rvdgssite6cj47gidfk6r6.apps.googleusercontent.com',
    'consumer_secret': 'uz35A0Ru88FzDj3YskNpBYbr',
    'id': authomatic.provider_id(),
    'scope': ['email', 'profile']
  },
  
  'gae_oi': {
    # OpenID provider based on Google App Engine Users API.
    # Works only on GAE and returns only the id and email of a user.
    # Moreover, the id is not available in the development environment!
    'class_': gaeopenid.GAEOpenID,
  }
}
