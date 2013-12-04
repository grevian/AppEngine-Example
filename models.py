from google.appengine.ext import ndb

class JedditUser(ndb.Model):
  user = ndb.UserProperty(required=True, indexed=False)
  joined = ndb.DateProperty(auto_now_add=True)
  about = ndb.TextProperty()

  # In case users don't want to display their Google "name", they can override it here
  local_nickname = ndb.StringProperty(indexed=False)

  @classmethod
  def key_from_user(cls, user):
    # Construct the key using the user_id that is assured to be constant as our identifier
    # This also serves as a good example of how to tie entities together without requiring a query
    return ndb.Key('JedditUser', user.user_id())

  @classmethod
  def create(cls, user):
    key = cls.key_from_user(user)
    return cls(key=key, user=user)

  @classmethod
  def get_by_user(cls, user):
    key = cls.key_from_user(user)
    return key.get()    

  @property
  def nickname(self):
    if self.local_nickname:
      return self.local_nickname
    else:
      return self.user.nickname()

# Our basic user submitted content
class Article(ndb.Model):
  title = ndb.StringProperty(required=True)
  content = ndb.TextProperty(required=True)
  submitted = ndb.DateTimeProperty(auto_now_add=True)
  submitter = ndb.KeyProperty(kind=JedditUser)
  rating = ndb.FloatProperty(default=0.5)

# Two models used to calculate the content rating
class Upvote(ndb.Model):
  article = ndb.KeyProperty(kind=Article)
  user = ndb.KeyProperty(kind=JedditUser)
  voted = ndb.DateTimeProperty(auto_now_add=True)

class Downvote(ndb.Model):
  article = ndb.KeyProperty(kind=Article)
  user = ndb.KeyProperty(kind=JedditUser)
  voted = ndb.DateTimeProperty(auto_now_add=True)


