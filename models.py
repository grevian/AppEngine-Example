from google.appengine.ext import ndb

# Our basic user submitted content
class Article(ndb.Model):
  title = ndb.StringProperty(required=True)
  content = ndb.StringProperty(required=True)
  submitted = ndb.DateTimeProperty(auto_now_add=True)
  rating = ndb.FloatProperty(default=1.0)

# Two models used to calculate the content rating
class Upvote(db.Model):
  article = ndb.KeyProperty(kind=Article)
  voted = ndb.DateTimeProperty(auto_now_add=True)

class Downvote(db.Model):
  article = ndb.KeyProperty(kind=Article)
  voted = ndb.DateTimeProperty(auto_now_add=True)

