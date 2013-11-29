import jinja2
import logging
import os
import webapp2

from google.appengine.api import memcache

from models import Article

# This just says to load templates from the same directory this file exists in
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname('resources/templates/')))

class MainPage(webapp2.RequestHandler):

  def get(self): 
    """Generate the main index page"""
    # Check memcache for the list of front page articles
    articles_list = memcache.get("articles_list")

    # If it wasn't in memcache, generate the list and place it into memcache
    if not articles_list:
      articles = Article.query().order(-Article.rating, -Article.submitted).fetch(20)
      article_list = []
      for article in articles:
        article_properties = { 'title': article.title,
                               'rating': article.rating,
                               # This model unpacking is necessary to get the key/id
                               'id': article.key.id() }
        article_list.append(article_properties)
      memcache.add("articles_list", articles_list, time=60)

    # display the list of front page articles in the front page template
    template_values = {
      'articles': article_list,
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

    # Invalidate the article list in memcache, It will get rebuilt next time the front page is loaded
    memcache.delete("articles_list")

    return self.redirect('/article/%d' % article_key.id(), body="Thanks for your submission!")

class ArticleView(webapp2.RequestHandler):

  def get(self, article_id):
    """Generate a page for a specific article"""
    article = Article.get_by_id(int(article_id))
    template_values = {
      'title': article.title,
      'content': article.content,
      'date': article.submitted,
      'rating': article.rating,
      'id': article_id,
    }

    template = jinja_environment.get_template('article.html')
    self.response.out.write(template.render(template_values))

# Here we can set up more advanced routing rules
APP = webapp2.WSGIApplication([
    (r'/', MainPage),
    (r'/submit', Submit),
    (r'/article/(\d+)', ArticleView),
], debug=True)

