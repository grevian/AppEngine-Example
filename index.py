import jinja2
import logging
import os
import webapp2

from google.appengine.api import memcache
from google.appengine.api import users

from models import Article, JedditUser

# This just says to load templates from the same directory this file exists in
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname('resources/templates/')))

class MainPage(webapp2.RequestHandler):

  def get(self): 
    """Generate the main index page"""
    template_values = {}

    user = users.get_current_user()
    if user:
      template_values['user'] = JedditUser.get_or_create_by_user(user)
      template_values['google_logout_url'] = users.create_logout_url('/')
    else:
      template_values['google_login_url'] = users.create_login_url('/login')

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
                               'id': article.key.id(),
                               'submitted': article.submitted
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

class Login(webapp2.RequestHandler):

  def post(self):
      # Here you could attempt to create an account through other APIs that could have been passed in
      # Or log them into your local API using a username/password in self.request.POST perhaps
      # but for this app, we just give up and tell them we couldn't figure it out.
      self.response.write('You could not be logged in')

  def get(self):
    # Get the logged in user from the Google Users API
    # https://developers.google.com/appengine/docs/python/users/
    user = users.get_current_user()
    if user:
      # Use a user entity in our datastore so we can get their nickname etc. for other users to see
      # Also to tie content created by them on Jeddit back to their user account
      existing_user = JedditUser.get_or_create_by_user(user)
      
      # The docs indicate that an existing user could change their email address or nickname, which could require
      # the user entity to be updated, so handle that case here
      if existing_user.user != user:
        existing_user.user = user
        new_user.put()
      return self.redirect('/', body="Thanks for logging in")
    else:
      # You could display a login form here if you had alternative methods of logging in
      self.response.write('You could not be logged in')

class Submit(webapp2.RequestHandler):

  def post(self):
    article = Article(title=self.request.POST['article-title'], content=self.request.POST['article-content'])

    # Attach our user if the submitter is logged in, but we do allow anonymous posts
    user = users.get_current_user()
    if user:
      article.submitter = JedditUser.key_from_user(user)
    article_key = article.put()

    # Invalidate the article list in memcache, It will get rebuilt next time the front page is loaded
    memcache.delete("articles_list")

    # Redirect on POST is a common web technique, designed to keep people from accidentally
    # resubmitting the same form repeatedly
    return self.redirect('/article/%d' % article_key.id(), body="Thanks for your submission!")

class ArticleView(webapp2.RequestHandler):

  def get(self, article_id):
    """Generate a page for a specific article"""
    template_values = {}

    user = users.get_current_user()
    if user:
      template_values['user'] = user
      template_values['google_logout_url'] = users.create_logout_url('/')
    else:
      template_values['google_login_url'] = users.create_login_url('/login')

    article = Article.get_by_id(int(article_id))
    article_values = {
      'title': article.title,
      'content': article.content,
      'submitted': article.submitted,
      'rating': article.rating,
      'id': article_id,
    }

    if article.submitter:
      submitter = article.submitter.get()
      if submitter:
        article_values['submitter'] = submitter.nickname

    # Merge the two sets of variables together
    template_values.update(article_values)

    template = jinja_environment.get_template('article.html')
    self.response.out.write(template.render(template_values))

# Here we can set up more advanced routing rules
APP = webapp2.WSGIApplication([
    (r'/', MainPage),
    (r'/submit', Submit),
    (r'/login', Login),
    (r'/article/(\d+)', ArticleView),
], debug=True)

