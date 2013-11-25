import webapp2
import jinja2
import os

from models import Article

# This just says to load templates from the same directory this file exists in
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Vote(webapp2.RequestHandler):

  def post(self): 
    article_id = request.POST['article_id']
    if not article_id:
      self.abort(404)
    
    article = Article.get_by_id(article_id)
    
    if request.POST['type'] == 'down':
      vote = Upvote(article=article)
    else:
      vote = Downvote(article=article)

    vote.put()

    template = jinja_environment.get_template('voted.html')
    self.response.out.write(template.render({'article_id': article_id}))

