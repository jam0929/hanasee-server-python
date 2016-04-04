import datetime, time
import re
from google.appengine.ext import ndb

class InitModel(ndb.Expando):
  def __init__(self, *args, **kwargs):
    id = self.allocate_ids(1)[0] if kwargs.get('auto_id') else None

    if id is None:
      super(InitModel, self).__init__(*args, **kwargs)
    else:
      parent = kwargs.get('parent')
      super(InitModel, self).__init__(key = self.get(id=id, parent=parent))

  # create new entity with id
  #@ndb.transactional
  def set(self, reqInfo):
    if not self:
      return None
    else:
      for item in reqInfo.keys():
        if hasattr(self, item):
          if not isinstance(getattr(self, item), list):
            reqInfo[item] = reqInfo[item][0] if isinstance(reqInfo[item], list) else reqInfo[item]
          else:
            reqInfo[item] = reqInfo[item] if isinstance(reqInfo[item], list) else [reqInfo[item]]

          if type(getattr(self, item)) == int:
            if bool(re.search('[+-]\d', reqInfo[item])):
              setattr(self, item, getattr(self, item) + int(re.compile('[+]?([-]?\d)').search(reqInfo[item]).group(1)))
            else:
              setattr(self, item, (int)(reqInfo[item]))
          elif type(getattr(self, item)) == datetime.datetime:
            setattr(self, item, datetime.datetime.fromtimestamp(int(reqInfo[item]) / 1e3))
          else:
            setattr(self, item, reqInfo[item])
        else:
          setattr(self, item, reqInfo[item][0] if hasattr(reqInfo[item], '__iter__') else reqInfo[item])

      return self.put()

  # get an entity
  # return entity if exists
  # otherwise, return key
  @classmethod
  @ndb.transactional
  def get(cls, **kwargs):
    key = ndb.Key(cls, kwargs.get('id'), parent=kwargs.get('parent'))
    item = key.get()

    if item is None:
      return key
    else:
      return item


  def to_obj(self, **kwargs):
    result = {}
    exceptList = kwargs.get('except_list', [])

    for item in self._properties:
      if item in exceptList:
        pass
      elif type(getattr(self, item)) == ndb.key.Key:
        if getattr(self, item).get():
          result[item] = getattr(self, item).get().to_obj()
      elif type(getattr(self, item)) == type(datetime.datetime.now()):
        result[item] = "%d" % (time.mktime(getattr(self, item).timetuple())*1e3 + getattr(self, item).microsecond/1e3)
      else:
        result[item] = getattr(self, item)
    if self.key:
      result[kwargs.get('id_name', 'id')] = self.key.id()
      if self.key.parent():
        if self.key.parent().get():
          result[kwargs.get('parent_name', 'parent')] = self.key.parent().get().to_obj()
        else:
          result[kwargs.get('parent_name', 'parent')] = None

    return result

  @classmethod
  def delete_all(cls):
    keys = cls.query().fetch(keys_only=True)
    ndb.delete_multi(keys)

  @classmethod
  def up(cls):
    keys = cls.query().fetch(keys_only=True)
    for key in keys:
      item = key.get()
      setattr(item, 'country', 'kr')
      item.put()