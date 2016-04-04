from init import InitModel
from hanasies import Hanasies
from google.appengine.ext import ndb

class Channels(InitModel):
  name = ndb.StringProperty(required=True)
  order = ndb.IntegerProperty(default=999)

  @staticmethod
  def get(country):
    channels = Channels.query().fetch()

    for x in xrange(0, len(channels)):
      setattr(channels[x], 'count', Hanasies.get_channel_count(getattr(channels[x],'name'), country))

    return channels

  @staticmethod
  def set(_name, _order):
    key = ndb.Key(Channels, _name)
    channel = key.get()
    if channel is None:
      channel = Channels(key=key)

    setattr(channel, 'name', _name)
    setattr(channel, 'order', int(_order))
    channel.put()
    return channel
