import jinja2
import logging
import os
import webapp2

from google.appengine.api import memcache
from google.appengine.api import users

from index import MainPage
from auth import Login
from article import Submit, ArticleView, AddComment
from vote import Vote

# This just says to load templates from the same directory this file exists in
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname('resources/templates/')))

# Here we can set up more advanced routing rules
APP = webapp2.WSGIApplication([
    (r'/', MainPage),
    (r'/login', Login),
    (r'/submit', Submit),
    (r'/article/(\d+)', ArticleView),
    (r'/article/(\d+)/comment', AddComment),
    (r'/vote/(\d+)/(\w+)', Vote),
], debug=True)

