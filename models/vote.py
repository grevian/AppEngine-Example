from google.appengine.ext import ndb

from auth import JedditUser
from content import Article

UPVOTE = 1
DOWNVOTE = -1

# Two models used to calculate the content rating
class Vote(ndb.Model):
  article = ndb.KeyProperty(kind=Article)
  user = ndb.KeyProperty(kind=JedditUser)
  voted = ndb.DateTimeProperty(auto_now_add=True)
  value = ndb.IntegerProperty(choices=(UPVOTE,DOWNVOTE), required=True)

  @classmethod
  def create(cls, article_key, user_key, value):
    # Compose a key that ensures a user can only vote on the same article once
    # any other votes will just overwrite the same entity no matter the type
    key = ndb.Key('Vote', '%s:%s' % (article_key.id(), user_key.id()))
    return Vote(key=key, user=user_key, article=article_key, value=value)

class RatingsUpdateJob(ndb.Model):
  MARKER_ID = 'RATINGS_UPDATE_JOB'
  job_started = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
  job_updated = ndb.DateTimeProperty(auto_now=True, indexed=False)
  articles_updating = ndb.KeyProperty(kind=Article,repeated=True, indexed=False)

