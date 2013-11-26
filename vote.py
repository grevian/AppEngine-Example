import webapp2
import jinja2
import os

from google.appengine.ext import ndb

from models import Article

# This just says to load templates from the same directory this file exists in
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Vote(webapp2.RequestHandler):

  def post(self, article_id, vote_type): 
    article = Article.get_by_id(article_id)
    
    if vote_type == 'down':
      vote = Upvote(article=article)
      article.rating = article.rating + 1.0
    else:
      vote = Downvote(article=article)
      article.rating = article.rating - 1.0
    
    ndb.put_multi(article, vote)

    return self.redirect('/', body="Thanks for your vote!")

VOTE_APP = webapp2.WSGIApplication([
    (r'/vote/(\d+)/down', Vote, defaults={'type': 'down'}),
    (r'/vote/(\d+)/up', Vote, defaults={'type': 'up'}),
], debug=True)

