import jinja2
import logging
import os
import webapp2

from article import get_frontpage_articles
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

   # Add the article list to the template
    template_values['articles'] = get_frontpage_articles()

    # If users aren't logged in, I could cache and return the entire rendered front page
    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))

