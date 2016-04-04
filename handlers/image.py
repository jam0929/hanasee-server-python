import webapp2
from google.appengine.api import images
from google.appengine.ext import blobstore

class ImageHandler(webapp2.RequestHandler):
  def get(self, **kwargs):
    blob_key = kwargs.get('blobId')
    if blob_key:
      blob_info = blobstore.get(blob_key)

    if blob_info:
      img = images.Image(blob_key=blob_key)
      #img.resize(width=80, height=100)
      #img.im_feeling_lucky()
      #thumbnail = img.execute_transforms(output_encoding=images.JPEG)

      self.response.headers['Content-Type'] = 'image/jpeg'
      self.response.write(img)
      return

    # Either "blob_key" wasn't provided, or there was no value with that ID
    # in the Blobstore.
    self.error(404)