# -*- coding: utf-8 -*-
import time, datetime
from init import InitModel
from google.appengine.ext import ndb
import re
from google.appengine.datastore.datastore_query import Cursor
from likes import Likes
from hanasy_bookmarks import HanasyBookmarks
import logging

class Hanasies(InitModel):
  created = ndb.DateTimeProperty(default=datetime.datetime.now(), auto_now_add=True)
  updated = ndb.DateTimeProperty(default=datetime.datetime.now())
  channel = ndb.StringProperty(default='etc')
  title = ndb.StringProperty(required=True)
  description = ndb.TextProperty(required=True)
  status = ndb.StringProperty(default='ready')
  totalViewCount = ndb.IntegerProperty(default=0)
  viewCount = ndb.IntegerProperty(default=0)
  shareCount = ndb.IntegerProperty(default=0)
  likeCount = ndb.IntegerProperty(default=0)
  icon = ndb.StringProperty()
  thumbnails = ndb.StringProperty(repeated=True)
  images = ndb.StringProperty(repeated=True)
  tags = ndb.StringProperty(repeated=True)
  partCount = ndb.IntegerProperty(default=0)
  commentCount = ndb.IntegerProperty(default=0)

  def to_obj(self):
    return super(Hanasies, self).to_obj(id_name='sid', parent_name='Author')

  @classmethod
  def find(cls, options):
    qry = cls.query(ancestor = options.get('author'))
    cursor = Cursor(urlsafe=options.get('cursor'))

    # filters
    if options.get('channel', None):
      qry = qry.filter(cls.channel == options.get('channel'))
    if options.get('status', None):
      qry = qry.filter(cls.status == options.get('status'))
    if options.get('created', None):
      qry = qry.filter(cls.created == datetime.datetime.fromtimestamp(int(options.get('created')) / 1e3))
    if options.get('country', None):
      qry = qry.filter(ndb.GenericProperty('country') == options.get('country'))
    if options.get('search', None):
      qry = qry.filter(cls.tags == options.get('search'))
    if options.get('onair', None):
      dt = datetime.datetime.now() - datetime.timedelta(minutes=10)
      qry = qry.filter(cls.updated > dt).order(-cls.updated)

    # order
    if qry.count() > 0:
      order = options.get('order', None)
      if order in ['new', '-new']:
        order = cls.updated
      elif order in ['best', '-best']:
        order = cls.totalViewCount
      elif order in ['created', '-created']:
        order = -cls.created if options.get('order', 'new')[0] == '-' else cls.created
      else:
        order = cls.viewCount
      order = order if options.get('order', 'new')[0] == '-' else -order
      qry = qry.order(order)

      # set default sub order(created)
      qry = qry.order(-cls.created)

    if cursor:
      return qry.fetch_page(int(options.get('limit', 20)), start_cursor=cursor), qry.count()
    else:
      return qry.fetch_page(int(options.get('limit', 20))), qry.count()

  @classmethod
  def get_channel_count(cls, channel, country):
    qry = cls.query()
    qry = qry.filter(cls.channel == channel)
    if country:
      qry = qry.filter(ndb.GenericProperty('country') == country)
    return qry.count()

  @classmethod
  def get_actioned_user(cls, key):
    like_users = Likes.find(None, key)
    like_users = [like_user.user for like_user in like_users]

    bookmark_users = HanasyBookmarks.find_v2(key)
    bookmark_users = [bookmark_user.user for bookmark_user in bookmark_users]

    return list(set(like_users + bookmark_users))

  @classmethod
  def get_actioned_user_back(cls, key):
    like_users = Likes.find(None, key)
    like_users = [like_user.user.get() for like_user in like_users]
    like_users_reg_ids = [getattr(user, 'ssulit') for user in like_users if hasattr(user, 'ssulit')]
    like_users_emails = [getattr(user, 'email') for user in like_users if hasattr(user, 'email')]

    bookmark_users = HanasyBookmarks.find_v2(key)
    bookmark_users = [bookmark_user.user.get() for bookmark_user in bookmark_users]
    bookmark_users_reg_ids = [getattr(user, 'ssulit') for user in bookmark_users if hasattr(user, 'ssulit')]
    bookmark_users_emails = [getattr(user, 'email') for user in bookmark_users if hasattr(user, 'email')]

    return list(set(like_users_reg_ids + bookmark_users_reg_ids)), list(set(like_users_emails + bookmark_users_emails))
