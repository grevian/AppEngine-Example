import webapp2
import os

from google.appengine.ext import ndb

from models import Article, Upvote, Downvote

class Vote(webapp2.RequestHandler):

  def post(self, article_id, vote_type): 
    article = Article.get_by_id(int(article_id))
    
    if vote_type == 'down':
      vote = Upvote(article=article.key)
    else:
      vote = Downvote(article=article.key)
    
    vote.put()

    return self.redirect('/', body="Thanks for your vote!")

  def get(self, article_id, vote_type):
    return self.post(article_id, vote_type)

VOTE_APP = webapp2.WSGIApplication([
    (r'/vote/(\d+)/(\w+)', Vote),
], debug=True)

