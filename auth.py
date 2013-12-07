import logging
import webapp2

from google.appengine.api import users

from models.auth import JedditUser

class LoginHandler(webapp2.RequestHandler):

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
      logging.info("%s has logged in" % existing_user.user.email())
      
      # The docs indicate that an existing user could change their email address or nickname, which could require
      # the user entity to be updated, so handle that case here
      if existing_user.user != user:
        logging.info("User %s has updated their google account")
        existing_user.user = user
        new_user.put()

      if self.request.get('final'):
        return self.redirect(self.request.get('final'), body="Thanks for logging in")
        
      return self.redirect('/', body="Thanks for logging in")
    else:
      # You could display a login form here if you had alternative methods of logging in
      logging.warning("A user could not be logged in")
      self.response.write('You could not be logged in')

def user_vars():
    template_values = {}

    user = users.get_current_user()

    if user:
      template_values['user'] = JedditUser.get_or_create_by_user(user)
    else:
      template_values['google_login_url'] = users.create_login_url('/login')

    return template_values
