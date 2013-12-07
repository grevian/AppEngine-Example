import jinja2
import logging
import os
import webapp2

from google.appengine.api import memcache
from google.appengine.api import users

from models.content import Article, Comment
from auth import user_vars

# This just says to load templates from the same directory this file exists in
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname('resources/templates/')))

class IndexHandler(webapp2.RequestHandler):

  def get(self): 
    """Generate the main index page"""
    template_values = {}

    # Load any user specific values to pass into the template
    template_values.update(user_vars())

    # Check memcache for the list of front page articles
    articles_list = memcache.get("articles_list")

    # If it wasn't in memcache, generate the list and place it into memcache
    if not articles_list:
      logging.info("Front page not found in memcache, requerying")
      article_list = []
      articles = Article.query().order(-Article.rating, -Article.submitted).fetch(20)

      for article in articles:
        article_properties = { 'title': article.title,
                               'rating': article.rating,
                               'submitted': article.submitted,
                               'id': article.key.id(),
                               }

        # This is actually an anti-pattern, I should show the appstats waterfall here and have a PR to fix it
        # Though it does show exactly why you'd want to memcache a heavier object like this
        if article.submitter:
          submitter = article.submitter.get()
          # We test this in case a user was deleted
          if submitter:
            article_properties['submitter'] = submitter.nickname

        article_list.append(article_properties)
      memcache.add("articles_list", articles_list, time=60)

    # Add the article list to the template
    template_values['articles'] = article_list

    # If users aren't logged in, I could cache and return the entire rendered front page
    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))

