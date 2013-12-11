from google.appengine.ext import ndb

from auth import JedditUser

# Our basic user submitted content
class Article(ndb.Model):
  title = ndb.StringProperty(required=True)
  content = ndb.TextProperty(required=True)
  submitted = ndb.DateTimeProperty(auto_now_add=True)
  submitter = ndb.KeyProperty(kind=JedditUser)
  rating = ndb.FloatProperty(default=0.5)

class Comment(ndb.Model):
  article = ndb.KeyProperty(kind=Article)
  user = ndb.KeyProperty(kind=JedditUser)
  posted = ndb.DateTimeProperty(auto_now_add=True)
  content = ndb.TextProperty(required=True)

