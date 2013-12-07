import webapp2
import os

from google.appengine.ext import ndb
from google.appengine.api import users

from models.content import Article, Upvote, Downvote
from models.auth import JedditUser

class Vote(webapp2.RequestHandler):

  def post(self, article_id, vote_type): 
    article = Article.get_by_id(int(article_id))
    user = users.get_current_user()
    
    if vote_type == 'down':
      vote = Upvote(article=article.key)
      article.rating = article.rating - 1.0
    else:
      vote = Downvote(article=article.key)
      article.rating = article.rating + 1.0
    
    if user:
      vote.user = JedditUser.key_from_user(user)

    ndb.put_multi([article, vote])

    return self.redirect('/', body="Thanks for your vote!")

  def get(self, article_id, vote_type):
    return self.post(article_id, vote_type)

VOTE_APP = webapp2.WSGIApplication([
    (r'/vote/(\d+)/(\w+)', Vote),
], debug=True)

