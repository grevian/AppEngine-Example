import webapp2

from google.appengine.ext import ndb
from google.appengine.api import users

from models.content import Article
from models.vote import Vote
from models.vote import UPVOTE, DOWNVOTE
from models.auth import JedditUser

class AddVoteHandler(webapp2.RequestHandler):

  def post(self, article_id, vote_type): 
    article = Article.get_by_id(int(article_id))

    user = users.get_current_user()
    if user:
      user_key = JedditUser.key_from_user(user)
    
    if vote_type == 'down':
      vote = Vote.create(article_key=article.key, user_key=user_key, value=DOWNVOTE)
      article.rating = article.rating - 1.0
    else:
      vote = Vote.create(article_key=article.key, user_key=user_key, value=UPVOTE)
      article.rating = article.rating + 1.0

    ndb.put_multi([article, vote])

    return self.redirect('/', body="Thanks for your vote!")

  def get(self, article_id, vote_type):
    return self.post(article_id, vote_type)

