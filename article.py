import jinja2
import logging
import os
import webapp2

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.ext import deferred
from google.appengine.ext import ndb

from models.vote import RatingsUpdateJob
from models.content import Article, Comment
from models.auth import JedditUser
from vote import RATINGS_QUEUE, update_all_ratings

# This just says to load templates from the same directory this file exists in
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname('resources/templates/')))

class AddArticleHandler(webapp2.RequestHandler):

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

class AddCommentHandler(webapp2.RequestHandler):
  def post(self, article_id):
    article_id = int(article_id)
    google_user = users.get_current_user()
    user = JedditUser.get_or_create_by_user(google_user)
    article = Article.get_by_id(article_id)
    comment_content = self.request.POST['comment']
    if not comment_content or comment_content.strip() == '':
      return self.redirect('/article/%d' % article_id, body="Empty comment submitted")
    comment = Comment(user=user.key, article=article.key, content=comment_content)
    comment.put()
    return self.redirect('/article/%d' % article_id, body="Thank you for your comment")

class ViewArticleHandler(webapp2.RequestHandler):

  def get(self, article_id):
    """Generate a page for a specific article"""
    template_values = {}

    user = users.get_current_user()
    if user:
      template_values['user'] = user
      template_values['google_logout_url'] = users.create_logout_url('/')
    else:
      template_values['google_login_url'] = users.create_login_url('/login?final=/article/%d' % int(article_id))

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

    comment_list = []
    # Add in any comments that might exist
    for comment in Comment.query(Comment.article == article.key).order(Comment.posted):
      comment_values = {}
      comment_values['id'] = comment.key.id()
      # Another fine example of an anti-pattern
      comment_values['user'] = comment.user.get()
      comment_values['posted'] = comment.posted.strftime("%A, %d. %B %Y %I:%M%p")
      comment_values['content'] = comment.content
      comment_list.append(comment_values)

    template_values['comments'] = comment_list
    template = jinja_environment.get_template('article.html')
    self.response.out.write(template.render(template_values))


def get_frontpage_articles():
  # Check memcache for the list of front page articles
  articles_list = memcache.get("articles_list")

  # If it wasn't in memcache, generate the list and place it into memcache
  if not articles_list:
    # Check if article stats need an update, or is currently updating
    stats_future = taskqueue.QueueStatistics.fetch_async(RATINGS_QUEUE)

    # Query for the top 20 current articles
    articles_future = Article.query().order(-Article.rating, -Article.submitted).fetch_async(20)

    # We get the queue stats to see if any ratings updates are waiting to be applied
    stats = stats_future.get_result()
    # The marker existing means an update job is already in progress
    
    @ndb.transactional
    def update_ratings():
      marker_exists = RatingsUpdateJob.get_by_id(RatingsUpdateJob.MARKER_ID)
      if stats.tasks > 0 and not marker_exists:
        logging.info("Ratings updates are waiting to be applied, Queuing update task")
        RatingsUpdateJob(id=RatingsUpdateJob.MARKER_ID).put()
        deferred.defer(update_all_ratings)
    update_ratings()

    articles_list = build_article_list(articles_future.get_result())

    # Add the article list to memcache
    memcache.add("articles_list", articles_list, time=60)

  return articles_list

def build_article_list(articles):
  articles_list = []
  # Unpack the article entities
  for article in articles:
    article_properties = { 'title': article.title,
                           'rating': article.rating,
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
      
    articles_list.append(article_properties)

  return articles_list

