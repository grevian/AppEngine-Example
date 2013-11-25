import jinja2
import logging
import os
import webapp2

from models import Article

# This just says to load templates from the same directory this file exists in
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class MainPage(webapp2.RequestHandler):

  def get(self): 
    """Generate the main index page"""
    articles = Article.query().order(Article.rating)
    template_values = {
      'articles': articles,
    }

    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))

class Submit(webapp2.RequestHandler):

  def get(self):
    template = jinja_environment.get_template('submit.html')
    self.response.out.write(template.render(template_values))

  def post(self):
    article = Article(title=self.request.POST['article-title'], content=self.request.POST['article-content'])
    article_key = article.put()
    return self.redirect('/article/%d' % article_key.id(), body="Thanks for your submission!")

class ArticleView(webapp2.RequestHandler):

  def get(self, article_id):
    """Generate a page for a specific article"""
    article = Article.get_by_id(article_id)
    template_values = {
      'title': article.title,
      'content': article.content,
      'date': article.date,
      'rating': article.rating,
      'id': article.id,
    }

    template = jinja_environment.get_template('article.html')
    self.response.out.write(template.render(template_values))

# Here we can set up more advanced routing rules
APP = webapp2.WSGIApplication([
    (r'/', MainPage),
    (r'/submit', Submit),
    (r'/article/(<article_id:\d+>)', ArticleView),
], debug=True)

